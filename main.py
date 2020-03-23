from packages.pipes import prefabs
from packages.pipes.pipeline import Pipeline

# This file is meant to be an example at
# the time of writing. Uncomment blocks
# for testing (max one at a time)


# prefabs.get_pipeline_api_cln_simi_db(
#     api_track=["to", "and", "from", "but", "how"]
# ).run()


# prefabs.get_pipeline_dsk_cln_simi_db(
#     filepath="200322-18_57_08--200322-18_57_08"
# ).run()


# prefabs.get_pipeline_dsk_cln_simi_js(
#     filepath="200322-18_57_08--200322-18_57_08",
#     initial_query=["corona", "virus", "death", "sick", "help"]
# )


prefabs.get_pipeline_api_cln_simi_js(
    api_track=["to", "and", "from", "but", "how"],
    initial_query=["corona", "virus", "death", "sick", "help"]
).run()

print("end")