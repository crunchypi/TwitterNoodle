 // Twitter (Tweepy) API credentials.
consumer_key = ""
consumer_secret = ""
token_key = ""
token_secret = ""
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(token_key, token_secret)

# // Neo4j login - set as defaults
neo4j_uri = "bolt://localhost:7687"
neo4j_user_name = "neo4j"
neo4j_password = "neo4j"

# // Server conf
pyjs_bridge_ip = "127.0.0.1"
pyjs_bridge_port = 5678
