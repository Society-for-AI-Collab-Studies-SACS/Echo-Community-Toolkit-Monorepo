from echo_soulcode.schema import validate_bundle
from tests.test_schema_single_minimal import minimal_single

def test_validate_bundle_minimal():
    bundle = {
        "ECHO_SQUIRREL": minimal_single(),
        "ECHO_FOX": minimal_single(),
        "ECHO_PARADOX": minimal_single()
    }
    validate_bundle(bundle)
