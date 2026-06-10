import os
from ecg2sca import cli


def test_self_check_files_exist():
    # Use repo-local model paths (should exist in this workspace)
    encoder = os.path.join(os.path.dirname(__file__), os.pardir, "models", "encoder_median.h5")
    encoder = os.path.normpath(encoder)
    bundle = os.path.join(os.path.dirname(__file__), os.pardir, "models", "lasso_logreg_bundle.joblib")
    bundle = os.path.normpath(bundle)

    res = cli.self_test(encoder, bundle, run_encoder=False)
    assert "encoder_file_exists" in res
    assert "bundle_file_exists" in res
    # The test is mainly to detect missing files or imports; it should return booleans
    assert isinstance(res["encoder_file_exists"], bool)
    assert isinstance(res["bundle_file_exists"], bool)
