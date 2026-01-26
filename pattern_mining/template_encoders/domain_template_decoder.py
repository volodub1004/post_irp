import unicodedata
import re
import pandas as pd
from typing import Dict, Any, List, Optional

# Define common suffices for investment firms
INVESTMENT_SUFFIXES = [
    "management",
    "mgmt",
    "group",
    "group",
    "grp",
    "capital",
    "cap" "partners",
    "prtnrs",
    "advisors",
    "advisory",
    "securities",
    "security" "investments",
    "investment",
    "investors",
    "investor",
    "invest",
    "holdings",
    "holding",
]

# Define common legal suffixes
LEGAL_SUFFIXES = ["llc", "inc", "corp", "ltd", "plc", "co"]


class DomainTemplateEncoder:
    """
    DomainTemplateEncoder encodes domain roots into structured token sequences based on firm names.

    This is used to uncover structural transformation patterns between a firm's name and its
    associated email domain. Each token sequence is suitable for SPMF-style sequential pattern
    mining, capturing prefix matches, abbreviations, and separator structure.

    Tokens are constructed by matching substrings from normalized firm name words to the domain
    root,
    with positional indexing (e.g. '0_sub_3') indicating which part of the firm name is matched and
    how.

    Note:
        This approach has been abandoned after EDA did not discover any notable trends in the
        template distribution or any related features.
    """

    def __init__(self):
        # Mapping from token to unique integer ID for SPMF input
        self.token_to_id: Dict[str, int] = {}

        # Maps integer ID back to token string for decoding output
        self.id_to_token: Dict[int, str] = {}

        # Statistics to track encoding progress and quality
        self.stats: Dict[str, Any] = {
            "total": 0,  # Total domains processed
            "unk_tokens": 0,  # Number of unknown tokens encountered
            "unk_sequences": [],  # Domains that contain unknown tokens
        }

        print("Domain Token Encoder Initialised!")

    def _normalize_firm_name(self, firm: str) -> str:
        """
        Normalizes a firm name by:
        - Lowercasing
        - Applying NFKD normalization to strip accents
        - Replacing dashes and slashes with spaces
        - Replace ampersand with "and"
        - Removing remaining punctuation

        Args:
            firm (str): Raw firm name

        Returns:
            str: Normalized, ASCII-safe version of the firm name
        """
        # Remove whitespace
        firm = firm.strip()
        # NFKD and to lower
        firm = unicodedata.normalize("NFKD", firm)
        firm = firm.encode("ascii", "ignore").decode("ascii").lower()
        # Replace dash and slash with spaces
        firm = re.sub(r"[-/]", " ", firm)
        # Replace ampersand with "and"
        firm = re.sub(r"&", "and", firm)
        # Remove remaining punctuation
        firm = re.sub(r"[^\w\s]", "", firm)
        # Collapse multiple spaces into one
        firm = re.sub(r"\s+", " ", firm)
        return firm

    def _to_firm_sequence(self, firm: str) -> List[str]:
        """
        Converts a normalized firm name string into a list of individual lowercase tokens.

        Args:
            firm (str): Raw firm name

        Returns:
            List[str]: Ordered list of normalized word tokens
        """
        # Normalize
        firm = self._normalize_firm_name(firm)
        # Split on space and return
        return firm.split()

    def _tokenize_firm_name(self, firm: str, domain: str) -> Optional[List[str]]:
        """
        Tokenizes a domain by matching structural segments against the normalized firm name.

        Attempts to match:
        - Full firm words
        - Prefix substrings of each word
        - Separators (e.g. '-', '_')
        Unmatched characters are labeled as 'UNK'.

        Args:
            firm (str): Raw firm name
            domain (str): Full domain

        Returns:
            List[str] or None: Structural token sequence (e.g. ['0', '1_sub_3']) or None if 'UNK'
            is encountered
        """
        # Split firm name into sequence of given strings
        firm_seq = self._to_firm_sequence(firm)
        # Split domain to get root
        domain_root = domain.lower().split(".")[0]

        i = 0
        tokens = []

        # Iterate through domain root and try to match tokens
        while i < len(domain_root):
            segment_matched = False

            # Try full words
            for idx, word in enumerate(firm_seq):
                if domain_root.startswith(word, i):
                    tokens.append(f"{idx}")
                    i += len(word)
                    segment_matched = True
                    break

            if segment_matched:
                continue

            # Try common suffixes
            for suffix in INVESTMENT_SUFFIXES + LEGAL_SUFFIXES:
                if domain_root.startswith(suffix, i):
                    tokens.append(f"{suffix}")
                    i += len(suffix)
                    segment_matched = True
                    break
            if segment_matched:
                continue

            # Try prefix substrings
            for idx, word in enumerate(firm_seq):
                for sub in range(len(word) - 1, 0, -1):  # len-1 down to 1
                    if domain_root.startswith(word[:sub], i):
                        tokens.append(f"{idx}_sub_{sub}")
                        i += sub
                        segment_matched = True
                        break
                if segment_matched:
                    break

            if segment_matched:
                continue

            # Test separators
            if domain_root[i] in {"-", "_"}:
                tokens.append(domain_root[i])
            else:
                tokens.append("UNK")
            i += 1

        # Logging stats
        if "UNK" in tokens:
            self.stats["unk_sequences"].append([firm, domain_root])
            self.stats["unk_tokens"] += 1
            tokens = None
        self.stats["total"] += 1
        return tokens

    def encode_dataframe(self, df: pd.DataFrame) -> List[List[int]]:
        """
        Encodes all (firm, domain) pairs in a DataFrame into integer token sequences.

        Adds a 'domain_token_seq' column to the input DataFrame containing the raw token sequences.
        Also returns the integer-encoded sequences for use in sequential mining.

        Args:
            df (pd.DataFrame): DataFrame containing 'firm' (firm name) and 'domain' columns

        Returns:
            List[List[int]]: List of encoded domain sequences
        """
        required = ["domain", "firm"]
        for req in required:
            if req not in df.columns:
                raise ValueError(f"Required columns '{req}' not in DataFrame!")

        counter = 0
        token_seqs = []

        # Create token sequence field
        df["domain_token_seq"] = None

        # Iterate through each row in DataFrame and tokenise
        for i, (name, domain) in enumerate(zip(df["firm"], df["domain"])):
            # Print every 5000 steps to track progress
            if counter % 5000 == 0:
                print(f"Tokenised {counter} out of {df.shape[0]}")

            # Tokenise
            tokens = self._tokenize_firm_name(name, domain)
            if tokens:
                token_seqs.append(tokens)
                df.at[i, "domain_token_seq"] = tuple(tokens)
                counter += 1

        # Build lookup tables
        self._build_vocab(token_seqs)
        # Encode tokenises sequences into token ids for SPMF
        return self._encode_token_sequences(token_seqs)

    def _build_vocab(self, token_seqs: List[List[str]]) -> None:
        """
        Builds the internal vocabulary mapping token strings to unique integer IDs.

        Args:
            token_seqs (List[List[str]]): Raw token sequences

        Returns:
            None
        """
        # Iterate through each token
        for seq in token_seqs:
            for token in seq:
                # Index each token from 1 and add both ways
                if token not in self.token_to_id:
                    idx = len(self.token_to_id) + 1
                    self.token_to_id[token] = idx
                    self.id_to_token[idx] = token

    def _encode_token_sequences(self, token_seqs: List[List[str]]) -> List[List[int]]:
        """
        Encodes token sequences into integer ID sequences using the internal vocabulary.

        Args:
            token_seqs (List[List[str]]): Raw string token sequences

        Returns:
            List[List[int]]: Integer-encoded sequences
        """
        return [[self.token_to_id[token] for token in seq] for seq in token_seqs]
