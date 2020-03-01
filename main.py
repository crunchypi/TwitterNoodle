from packages.pipes import prefabs

pipeline = prefabs.get_pipeline_api_cln_simi_js(
    track_api=["to", "and", "from", "but", "how", "i", ],
    track_incident=["corona", "virus", "outbreak", "death", "sick"]
)

pipeline()
print("Done.")