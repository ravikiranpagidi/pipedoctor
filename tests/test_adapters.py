from pipedoctor.adapters.base import engine_name


def test_engine_name_accepts_pandas_top_level_module_shape():
    DataFrame = type("DataFrame", (), {"__module__": "pandas"})

    assert engine_name(DataFrame()) == "pandas"
