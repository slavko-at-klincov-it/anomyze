"""Austrian-specific detection patterns for Anomyze.

Re-exports all pattern modules for backwards compatibility.
"""

from anomyze.patterns.addresses import find_address_regex
from anomyze.patterns.blacklist import ENTITY_BLACKLIST, is_blacklisted
from anomyze.patterns.company_context import COMPANY_CONTEXT_PATTERNS, NORMAL_CONTEXT_WORDS
from anomyze.patterns.dates import find_birth_date_regex
from anomyze.patterns.documents import (
    find_aktenzahl_regex,
    find_id_card_regex,
    find_passport_regex,
)
from anomyze.patterns.email import find_emails_regex
from anomyze.patterns.financial import find_ibans_regex, find_svnr_regex, find_tax_number_regex
from anomyze.patterns.names import find_labeled_names_regex, find_titled_names_regex
from anomyze.patterns.phone import find_phone_regex
from anomyze.patterns.vehicles import find_license_plate_regex

__all__ = [
    "COMPANY_CONTEXT_PATTERNS",
    "NORMAL_CONTEXT_WORDS",
    "ENTITY_BLACKLIST",
    "find_emails_regex",
    "find_titled_names_regex",
    "find_labeled_names_regex",
    "find_ibans_regex",
    "find_svnr_regex",
    "find_tax_number_regex",
    "find_birth_date_regex",
    "find_aktenzahl_regex",
    "find_passport_regex",
    "find_id_card_regex",
    "find_license_plate_regex",
    "find_phone_regex",
    "find_address_regex",
    "is_blacklisted",
]
