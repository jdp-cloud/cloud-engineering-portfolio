"""
===============================================================================

 Gen2X Security Engineering Platform

 Module:
     base_enum.py

 Description
 -----------------------------------------------------------------------------

 This module defines the Gen2XEnum class.

 Every enumeration used throughout the Gen2X Security Engineering Platform
 inherits from this class.

 Examples include:

     • RiskLevel
     • IndicatorType
     • ProviderStatus
     • ThreatCategory
     • ReportStatus
     • ResponseStatus

 Rather than allowing arbitrary string values throughout the platform,
 Gen2X uses strongly typed enumerations to define a common vocabulary.

 Why?

 Enterprise software becomes easier to maintain when every component speaks
 the same language.

 Instead of writing:

     risk = "HIGH"

     risk = "high"

     risk = "Critical"

 every component simply uses

     RiskLevel.HIGH

 This eliminates an entire class of programming errors while making the
 code significantly easier to read.

-------------------------------------------------------------------------------

 Responsibilities

    ✓ Shared enum behavior

    ✓ Serialization

    ✓ Validation

    ✓ Helper methods

    ✓ String conversion

    ✓ Documentation support

 Non-Responsibilities

    ✗ Threat Intelligence

    ✗ Providers

    ✗ Business Logic

    ✗ Reports

    ✗ AI

-------------------------------------------------------------------------------

 Architectural Pattern

 Gen2X follows a consistent package architecture.

    models/
        BaseModel

    providers/
        BaseProvider

    enums/
        Gen2XEnum

 Every package contains

    • shared behavior

    • specialized implementations

 This repetition is intentional.

 Once students understand one package,
 they can understand every package in the framework.

===============================================================================
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class Gen2XEnum(str, Enum):
    """
    Base class for every enumeration in Gen2X.

    This class centralizes behavior common to every enumeration used by the
    framework.

    Child enumerations inherit utility methods automatically, allowing
    developers to focus only on defining valid values.

    Example
    -------

    class RiskLevel(Gen2XEnum):

        LOW = "LOW"

        MEDIUM = "MEDIUM"

        HIGH = "HIGH"

        CRITICAL = "CRITICAL"

    Rather than writing helper functions for every enumeration,
    they are inherited from this class.
    """

    # ------------------------------------------------------------------
    # String Representation
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """
        Return the enum value.

        Example

            print(RiskLevel.HIGH)

        Output

            HIGH
        """
        return self.value

    # ------------------------------------------------------------------
    # Developer Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Friendly representation used while debugging.

        Example

            RiskLevel.HIGH
        """
        return f"{self.__class__.__name__}.{self.name}"

    # ------------------------------------------------------------------
    # Enumeration Names
    # ------------------------------------------------------------------

    @classmethod
    def names(cls) -> list[str]:
        """
        Return every enumeration name.

        Example

            RiskLevel.names()

        Returns

            [
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL"
            ]
        """
        return [member.name for member in cls]

    # ------------------------------------------------------------------
    # Enumeration Values
    # ------------------------------------------------------------------

    @classmethod
    def values(cls) -> list[str]:
        """
        Return every enumeration value.
        """
        return [member.value for member in cls]

    # ------------------------------------------------------------------
    # Enumeration Members
    # ------------------------------------------------------------------

    @classmethod
    def members(cls) -> list["Gen2XEnum"]:
        """
        Return every enumeration object.
        """
        return list(cls)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """
        Determine whether a value exists in this enumeration.

        Example

            RiskLevel.is_valid("HIGH")

        Returns

            True
        """
        return str(value).upper() in cls.values()

    # ------------------------------------------------------------------
    # String Conversion
    # ------------------------------------------------------------------

    @classmethod
    def from_string(cls, value: str) -> "Gen2XEnum":
        """
        Convert a string into an enumeration.

        The comparison is case-insensitive.

        Example

            RiskLevel.from_string("high")

        Returns

            RiskLevel.HIGH
        """

        value = value.upper()

        for member in cls:

            if member.value == value:

                return member

        raise ValueError(
            f"{value!r} is not a valid {cls.__name__}"
        )

    # ------------------------------------------------------------------
    # Documentation Hook
    # ------------------------------------------------------------------

    def describe(self) -> str:
        """
        Return a human-readable description.

        Child enumerations may override this method to provide
        domain-specific explanations.

        Example

            RiskLevel.HIGH.describe()

        Returns

            "High probability of malicious activity."

        The default implementation simply returns the enum value.
        """
        return self.value
