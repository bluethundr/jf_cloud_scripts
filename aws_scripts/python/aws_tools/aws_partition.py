from __future__ import annotations

from functools import lru_cache
from typing import Literal

import boto3

Partition = Literal["aws", "aws-us-gov", "aws-cn", "unknown"]

def _sts_region_for_profile(profile_name: str) -> str:
    """
    Pick an STS region that matches the profile's partition.
    If the profile region is us-gov-*, use that; otherwise use us-east-1.
    """
    s = boto3.Session(profile_name=profile_name)
    region = (s.region_name or "").strip().lower()

    if region.startswith("us-gov-"):
        # any gov region works for STS; use the configured one
        return region

    # Commercial default
    return "us-east-1"

@lru_cache(maxsize=256)
def get_partition(profile_name: str) -> Partition:
    sts_region = _sts_region_for_profile(profile_name)

    s = boto3.Session(profile_name=profile_name, region_name=sts_region)
    arn = s.client("sts", region_name=sts_region).get_caller_identity()["Arn"]

    parts = arn.split(":")
    if len(parts) >= 2 and parts[0] == "arn":
        return parts[1]  # aws / aws-us-gov / aws-cn
    return "unknown"

def is_gov(profile_name: str) -> bool:
    return get_partition(profile_name) == "aws-us-gov"