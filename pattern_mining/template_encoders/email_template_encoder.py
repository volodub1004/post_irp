import re
import unicodedata
import pandas as pd
from functools import lru_cache
from nameparser import HumanName
from typing import Dict, Any, List, Union, Optional, Tuple

# German transliteration map, NFKD will not recognize these
GERMAN_ASCII_MAP = {"ü": "ue", "ö": "oe", "ä": "ae", "ß": "ss", "ø": "o", "å": "aa"}
# Precompiled regex parsers for fast substitution
GERMAN_RE = re.compile("|".join(map(re.escape, GERMAN_ASCII_MAP)))


def _german_sub(match):
    """
    Substitute Germanic characters in a regex match object using the GERMAN_ASCII_MAP.

    Args:
        match (re.Match): A regex match object whose group(0) is a Germanic character.

    Returns:
        str: The ASCII equivalent from GERMAN_ASCII_MAP.
    """
    return GERMAN_ASCII_MAP[match.group(0)]


# For german or dutch names that use a surname particle
SURNAME_PARTICLES = {
    "vanden",
    "dela",
    "van",
    "der",
    "den",
    "del",
    "het",
    "ter",
    "ten",
    "von",
    "de",
    "op",
    "af",
    "di",
    "du",
    "la",
    "le",
}

# Email local part separators
SEPARATORS = {".", "-", "_"}


class EmailTemplateEncoder:
    """
    Encodes email local-parts into structured token sequences based on the associated full name.
    These token sequences represent syntactic templates (e.g. ["f", ".", "last"]) used for pattern
    mining.

    The encoder uses nameparser to break down names into parts and matches local-part components
    to name elements.
    It also maintains a mapping from token strings to integer IDs suitable for SPMF-style
    sequence mining.
    """

    def __init__(self):
        # Mapping from token to unique integer ID for SPMF input
        self.token_to_id: Dict[str, int] = {}

        # Maps integer ID back to token string for decoding output
        self.id_to_token: Dict[int, str] = {}

        # Statistics to track encoding progress and quality
        self.stats: Dict[str, Any] = {
            "total": 0,  # Total local-parts processed
            "unk_tokens": 0,  # Number of unknown tokens encountered
            "unk_sequences": [],  # Local email parts that contain unknown tokens
        }

        print("Email Token Encoder Initialised!")

    @staticmethod
    @lru_cache(maxsize=2048)  # Static memoized for efficiency
    def _transliterate_german(s: str) -> str:
        """
        Replaces German-specific accented characters with ASCII transliterations.

        Args:
            s (str): The input string.

        Returns:
            str: A string with German characters replaced by ASCII equivalents.
        """
        return GERMAN_RE.sub(_german_sub, s)

    @staticmethod
    @lru_cache(maxsize=2048)  # Static memoized for efficiency
    def _normalize_nfkd(s: str) -> str:
        """
        Applies NFKD Unicode normalization and strips accents producing
        an email safe, ASCII-only version of the string.

        Args:
            s (str): The input string.

        Returns:
            str: Normalized string.
        """
        return (
            unicodedata.normalize("NFKD", s)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )

    @staticmethod
    @lru_cache(maxsize=2048)  # Static memoized for efficiency
    def _generate_last_name_variants(surname: str) -> List[str]:
        """
        Generates possible composite variants of a surname, especially for names that include
        particles or prefixes common in Dutch and German.

        This is useful when the email local-part uses a collapsed or joined form of the last name,
        such as 'velden' from 'vandervelden'.

        Args:
            surname (str): The raw last name string, possibly containing particles.

        Returns:
            List[str]: A sorted list of possible joined last name variants.
        """
        # Add each particle to the surname in a set for reduced redundancy
        variants = {particle + surname for particle in SURNAME_PARTICLES}
        return sorted(variants, key=len, reverse=True)

    @lru_cache(maxsize=4096)
    def _generate_ascii_variants(
        self, string: str, surname: bool = False
    ) -> Dict[str, Optional[Union[str, List[str]]]]:
        """
        Generates a list of ASCII-safe variants of a name string for robust matching.

        This includes:
            - The original lowercase string
            - German-character transliteration
            - NFKD normalization
            - Combined transliteration + NFKD

        Args:
            noisy_strs (Union[str, List[str]]): The raw name string or list of strings.

        Returns:
            Dict[str]: A dictionary containing name variants:
                - original
                - translit
                - nfkd
                - nfkd_translit
        """
        # Normalize
        string = string.lower().strip()

        # Precompute variants
        translit = self._transliterate_german(string)
        nfkd = self._normalize_nfkd(string)
        nfkd_translit = self._normalize_nfkd(translit)

        # Build result dict
        result: Dict[str, Optional[Union[str, List[str]]]] = {
            "original": string,
            "translit": translit,
            "nfkd": nfkd,
            "nfkd_translit": nfkd_translit,
        }

        return result

    @lru_cache(maxsize=4096)
    def _decompose_name(self, full_name: str) -> Dict:
        """
        Decomposes a full name string into its components using nameparser.
        Also extracts initials for flexible tokenization.

        Args:
            full_name (str): The full name of the individual

        Returns:
            Dict[str, Any]:
                - 'first': first name
                - 'middle': list of middle name parts
                - 'last': last name as a single string
                - 'initials': dictionary with:
                    - 'f': first initial
                    - 'm': list of middle initials
                    - 'l': list of last name initials (splits on hyphens)

        Raises:
            ValueError: If nameparser returns a None object
        """
        # Decompose name with name parser
        name = HumanName(full_name)

        # Make sure key names are not empty
        if not name.first and not name.title:
            raise ValueError(f"Nameparser returned empty = {name.as_dict}")

        # Get first name (could be mistaken for title)
        first = name.first.lower() or name.title.lower()

        # Return decomposition
        return {
            "first": first.lower().replace("'", "").replace("-", " ").split(),
            "middle": name.middle.lower().replace("'", "").replace("-", " ").split(),
            "last": name.last.lower().replace("'", "").replace("-", " ").split(),
        }

    def _tokenize_local_part(
        self, local_part: str, name_parts: Dict
    ) -> Union[List[str], None]:
        """
        Tokenizes the email local-part into structural name-based tokens.

        Args:
            local_part (str): The part before the '@' in the email.
            name_parts (dict): Output of _decompose_name(). Includes first, middle,
            last, and initials.

        Returns:
            list[str]: A sequence of tokens (e.g. ['f', '.', 'last']) to be used for
            encoding/mining.
            None: If token sequence contains "UNK".
        """
        lp = local_part.lower()
        i = 0
        tokens = []

        # Prepare name variants
        part_variants = {
            "first": [self._generate_ascii_variants(f) for f in name_parts["first"]],
            "middle": [self._generate_ascii_variants(m) for m in name_parts["middle"]],
            "last": [
                self._generate_ascii_variants(la, True) for la in name_parts["last"]
            ],
        }

        # Define order of checks
        initials_order = [("f", "first"), ("m", "middle"), ("l", "last")]

        # Variant helper
        def _iter_variants(val):
            if isinstance(val, str):
                return [val]
            elif isinstance(val, list):
                return val
            return []

        while i < len(lp):
            segment_matched = False

            # Full string matches
            for label, variant_list in part_variants.items():
                for idx, variant_dict in enumerate(variant_list):
                    for variant_type, val in variant_dict.items():
                        for variant_str in _iter_variants(val):
                            if variant_str and lp.startswith(variant_str, i):
                                tokens.append(
                                    f"{label}_original_{idx}"
                                )  # Normalization variant does not affect token
                                i += len(variant_str)
                                segment_matched = True
                                break
                        if segment_matched:
                            break
                    if segment_matched:
                        break
                if segment_matched:
                    break

            # Initial matching - only matching given name initial
            if not segment_matched:
                for short, long in initials_order:
                    for idx, variant_dict in enumerate(part_variants[long]):
                        orig = variant_dict.get("original")
                        if orig and lp[i] == orig[0]:
                            tokens.append(f"{short}_{idx}")
                            i += 1
                            segment_matched = True
                            break
                    if segment_matched:
                        break

            # Fallback to separators or unknown
            if not segment_matched:
                char = lp[i]
                if char in SEPARATORS:
                    tokens.append(char)
                else:
                    tokens.append("UNK")
                    self.stats["unk_tokens"] += 1
                i += 1

        # Logging stats
        self.stats["total"] += 1
        if "UNK" in tokens:
            self.stats["unk_sequences"].append([name_parts, lp])
            return None
        return tokens

    def encode_dataframe(self, df: pd.DataFrame) -> List[List[int]]:
        """
        Tokenizes and encodes a DataFrame of names and emails into SPMF-ready sequences
        of integer tokens.
        Updates internal vocab lookup tables.

        Args:
            df (pd.DataFrame): Input data with full names and email addresses.

        Returns:
            List[List[int]]: Encoded token sequences suitable for TRuleGrowth.

        Raises:
            ValueError if required columns do not exist.
        """
        required = ["email", "investor"]
        for req in required:
            if req not in df.columns:
                raise ValueError(f"Required columns '{req}' not in DataFrame!")

        # Token sequence structures
        token_seqs = []
        token_seq_column: List[Optional[Tuple[str, ...]]] = [None] * len(df)
        failures = 0

        # Extract local part and domain
        df["local_part"] = df["email"].str.split("@").str[0]
        df["domain"] = df["email"].str.split("@").str[1]

        # Iterate through each row in DataFrame and tokenise
        for i, row in enumerate(df.itertuples(index=False)):
            # Print every 5000 steps to track progress
            if i % 5000 == 0 and i > 0:
                print(f"Tokenised {i} out of {df.shape[0]}")
            # Decompose
            try:
                name_parts = self._decompose_name(row.investor)
            except ValueError as ve:
                print(f"Name parsing failed on row {i} - {row} : {ve}")
                failures += 1
                continue

            # Tokenise
            tokens = self._tokenize_local_part(str(row.local_part), name_parts)
            if tokens:
                token_seqs.append(tokens)
                token_seq_column[i] = tuple(tokens)

        # Save to DataFrane
        df["token_seq"] = token_seq_column
        print(
            f"Finished tokenizing: {len(token_seqs)} valid rows, {failures} failures."
        )

        # Build lookup tables
        self._build_vocab(token_seqs)
        # Encode tokenises sequences into token ids for SPMF
        return self._encode_token_sequences(token_seqs)

    def _build_vocab(self, token_seqs: List[List[str]]) -> None:
        """
        Builds the internal vocabulary used to map string tokens to unique integer IDs.

        This function should be called once after all token sequences have been generated.
        It assigns each unique token a sequential integer ID starting from 1, and populates
        both `token_to_id` (string -> int) and `id_to_token` (int -> string) mappings.

        Args:
            token_seqs (List[List[str]]): A list of tokenized sequences, where each sequence is a
            list of string tokens.

        Returns:
            None: Modifies internal state in-place.
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
        Encodes a list of tokenized string sequences into lists of integer IDs using the current
        vocabulary.

        This function assumes `self._build_vocab()` has already been called to populate
        `token_to_id`.

        Args:
            token_seqs (List[List[str]]): A list of sequences, where each sequence is a list of
            string tokens.

        Returns:
            List[List[int]]: A list of sequences, where each string token has been replaced with
            its integer ID.
        """
        return [[self.token_to_id[token] for token in seq] for seq in token_seqs]

    def decode_token_sequence(self, token_ids: List[int]) -> List[str]:
        """
        Decodes a list of integer token IDs into their corresponding string tokens.

        This is the inverse operation of `_encode_token_sequences` and is useful for converting
        mined or stored sequences back into human-readable form.

        Args:
            token_ids (List[int]): A sequence of token IDs as produced by `encode_dataframe()` or
                                other encoded sources.

        Returns:
            List[str]: The corresponding list of token strings.

        Raises:
            KeyError: If any token ID is not found in `id_to_token`.
        """
        return [self.id_to_token[token_id] for token_id in token_ids]
