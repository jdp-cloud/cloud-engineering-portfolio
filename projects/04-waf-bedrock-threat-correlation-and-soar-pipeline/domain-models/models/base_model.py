"""
===============================================================================
 Gen2X Security Engineering Platform

 Module: base_model.py

 Description:
 ------------
 This module defines Gen2XModel, the base class for every domain model
 in the Gen2X platform.

 Examples include:

     • Indicator
     • ThreatEvidence
     • Threat
     • Provider
     • Report
     • Response

 Gen2XModel is built on pydantic.

 pydantic validates every model automatically:

     • at construction

     • on every field assignment

     • during deserialization

 Rather than writing validation, serialization, and copying by hand in
 every model, domain models inherit that behavior here — exactly the way
 every enumeration inherits shared behavior from Gen2XEnum.

 Responsibilities
 ----------------

 ✔ Shared model configuration
 ✔ Serialization (to_dict / to_json)
 ✔ Deserialization (from_dict)
 ✔ Object copying
 ✔ Utility helpers

 Non-Responsibilities
 --------------------

 ✘ Threat Intelligence
 ✘ AWS
 ✘ Provider Logic
 ✘ HTTP
 ✘ Databases
 ✘ Risk Scoring
 ✘ AI
 ✘ Report Generation

 Educational Notes
 -----------------

 The helper names below (to_dict, from_dict, to_json) are thin wrappers
 around pydantic's standard API (model_dump, model_validate,
 model_dump_json).

 Learn the Gen2X names to understand the framework.

 Learn the pydantic names to understand the industry.

 They are one line apart.

===============================================================================
"""

from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Type
from typing import TypeVar

try:
    from pydantic import BaseModel as PydanticBaseModel
    from pydantic import ConfigDict
except ImportError as import_error:  # pragma: no cover
    raise ImportError(
        "The Gen2X models package requires pydantic. "
        "Install dependencies with: pip install -r requirements.txt"
    ) from import_error

# ============================================================================
# Generic Type Variable
# ============================================================================

T = TypeVar("T", bound="Gen2XModel")


# ============================================================================
# Gen2X Model
# ============================================================================

class Gen2XModel(PydanticBaseModel):
    """
    Base class for every Gen2X domain model.

    Configuration decisions made here apply to the entire platform:

        validate_assignment=True

            Models re-validate whenever a field is assigned.

            An invalid mutation fails at the moment it happens,
            not three components later.

        extra="forbid"

            Unknown constructor arguments are rejected.

            Typos fail loudly instead of being silently absorbed.

    Child models declare fields and validators.

    Everything else is inherited.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    # ----------------------------------------------------------------------
    # Dictionary Serialization
    # ----------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this model into a JSON-safe dictionary.

        The output contains only JSON-compatible values:

            • Nested models become dictionaries

            • Enumerations become their string values

            • Datetimes become ISO-8601 strings

            • Sets become lists

        The output of to_dict() can always be passed back into
        from_dict() to reconstruct an equal object.

        Returns
        -------
        dict
        """

        return self.model_dump(mode="json")

    # ----------------------------------------------------------------------
    # JSON Serialization
    # ----------------------------------------------------------------------

    def to_json(self, indent: int = 4) -> str:
        """
        Serialize this model into JSON.

        Keys are sorted so output remains stable and diff-friendly.

        Parameters
        ----------
        indent
            Number of spaces used for formatting.

        Returns
        -------
        str
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

    # ----------------------------------------------------------------------
    # Deserialization
    # ----------------------------------------------------------------------

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Construct a model from a dictionary.

        Values are converted back into their declared field types:

            • Nested dictionaries become nested models

            • Enum values become enumeration members

            • ISO-8601 strings become datetimes

            • Lists become sets where the field declares a set

        Unknown top-level fields are ignored.

        Deserialization is intentionally forgiving about unknown
        fields because payloads often carry extra keys added by
        other systems.

        Direct construction remains strict (extra="forbid").

        Invalid or missing required values raise ValueError
        (pydantic's ValidationError is a ValueError).

        Returns
        -------
        Gen2XModel
        """

        filtered = {
            key: value
            for key, value in data.items()
            if key in cls.model_fields
        }

        return cls.model_validate(filtered)

    # ----------------------------------------------------------------------
    # Object Copy
    # ----------------------------------------------------------------------

    def copy(self: T) -> T:  # type: ignore[override]
        """
        Create a deep copy of this model.

        Returns
        -------
        Gen2XModel
        """

        return self.model_copy(deep=True)

    # ----------------------------------------------------------------------
    # Equality Helper
    # ----------------------------------------------------------------------

    def equals(self, other: object) -> bool:
        """
        Compare two models.

        This is equivalent to == but
        reads more naturally for some students.
        """

        return self == other

    # ----------------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        """
        Returns the class name.

        Example

            Indicator

            ThreatSummary

            Recommendation
        """

        return self.__class__.__name__

    # ----------------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------------

    @property
    def field_names(self) -> list[str]:
        """
        Return every declared field name.
        """

        return list(type(self).model_fields)

    # ----------------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------------

    def field_count(self) -> int:
        """
        Return the number of declared fields.
        """

        return len(type(self).model_fields)


# ============================================================================
#
# Chewbacca's Commentary 🐾
#
# Validation used to be
#
# a chore.
#
# Something engineers wrote
#
# by hand,
#
# at midnight,
#
# inconsistently.
#
# Gen2XModel makes validation
#
# a property of the platform.
#
# Every model.
#
# Every field.
#
# Every assignment.
#
# Automatically.
#
# Declare what should be true.
#
# Let the framework
#
# keep it true.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# ============================================================================


# ============================================================================
# Backwards-Compatible Alias
# ============================================================================
#
# Earlier revisions exported this class as BaseModel.
#
# New code should inherit from Gen2XModel.
#
# ============================================================================

BaseModel = Gen2XModel
