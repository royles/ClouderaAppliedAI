"""Map UI region selections to Bedrock client regions and inference profile IDs."""

# Geo scopes in the region dropdown (not valid boto3 region names).
GEO_SCOPES = frozenset({"global", "eu", "us", "au"})

# Real AWS region used for the bedrock-runtime client for each geo scope.
GEO_CLIENT_REGIONS: dict[str, str] = {
    "global": "us-east-1",
    "us": "us-east-1",
    "eu": "eu-west-1",
    "au": "ap-southeast-2",
}


def is_geo_scope(region: str) -> bool:
    return region in GEO_SCOPES


def resolve_bedrock_client_region(ui_region: str) -> str:
    """Return a real AWS region for boto3 bedrock-runtime clients."""
    return GEO_CLIENT_REGIONS.get(ui_region, ui_region)


def resolve_inference_model_id(base_model_id: str, ui_region: str) -> str:
    """
    Return the model / inference-profile ID to pass to InvokeModel.

    Geo scopes (global, eu, us, au) require prefixed inference profile IDs such as
    `global.anthropic.claude-sonnet-5`. Standard AWS regions use the base model ID.
    """
    if any(base_model_id.startswith(f"{scope}.") for scope in GEO_SCOPES):
        return base_model_id
    if ui_region in GEO_SCOPES:
        return f"{ui_region}.{base_model_id}"
    return base_model_id
