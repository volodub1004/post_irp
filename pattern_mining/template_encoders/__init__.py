"""
pattern_mining.template_encoders

Package for template encoders. Includes email encoder and domain encoder.
"""

from .email_template_encoder import EmailTemplateEncoder
from .domain_template_decoder import DomainTemplateEncoder

__all__ = [
    "EmailTemplateEncoder",
    "DomainTemplateEncoder",
]
