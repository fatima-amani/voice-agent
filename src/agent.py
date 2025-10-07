from livekit.agents import function_tool, Agent, RunContext
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, google, silero
from typing import Any

from tools.graph_tool import neo4j_tool
from tools.mongo_tool import mongo_tool


class ProductRecommenderAgent(Agent):

    @function_tool()
    async def neo4j(query: str) -> dict:
        """
        Query product graph database using natural language. Returns raw JSON data.
        
        Translates questions like 'find products by brand' into Cypher queries and 
        returns direct database results without additional processing.
        
        Args:
            user_query: Natural language question about products, brands, categories, etc.
        
        Returns:
            Raw JSON results from graph database query execution.
        
        Example: neo4j_tool('Show luxury brands') -> [{'brand': 'Prada'}, ...]
        """
        return neo4j_tool(query)
    
    @function_tool()
    async def mongo(query: str) -> list:
        """
    Query MongoDB with natural language. Returns raw JSON results.
    
    Args:
        user_query: Question about products, reviews, users, etc.
    
    Returns:
        list: Raw JSON data from the MongoDB query.
    
    Example:
        query = "find reviews for product 2"
        returns [{"review": "Great product", "rating": 5}]
    """
        return mongo_tool(query)

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = ProductRecommenderAgent(
        instructions="You are a friendly voice assistant built by LiveKit.",
        tools=[ProductRecommenderAgent.neo4j, ProductRecommenderAgent.mongo],
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=deepgram.TTS(),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="greet the user and ask about their day")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))