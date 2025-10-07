from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, google, silero

from prompts.agent import get_agent_instruction
from tools.graph_tool import neo4j_tool
from tools.mongo_tool import mongo_tool


@function_tool()
async def neo4j(query: str) -> dict:
    """
    Query product graph database using natural language. Returns raw JSON data.
    
    Translates questions like 'find products by brand' into Cypher queries and 
    returns direct database results without additional processing.
    
    Args:
        query: Natural language question about products, brands, categories, etc.
    
    Returns:
        Raw JSON results from graph database query execution.
    
    Example: neo4j('Show luxury brands') -> {'result': [{'brand': 'Prada'}, ...]}
    """
    return neo4j_tool(query)

@function_tool()
async def mongo(query: str) -> list:
    """
    Query MongoDB with natural language. Returns raw JSON results.
    
    Args:
        query: Question about products, reviews, users, etc.
    
    Returns:
        list: Raw JSON data from the MongoDB query.
    
    Example:
        mongo("find reviews for product 2") -> [{"review": "Great product", "rating": 5}]
    """
    return mongo_tool(query)


class ProductRecommenderAgent(Agent):
    pass

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = ProductRecommenderAgent(
        instructions=get_agent_instruction(),
        tools=[neo4j, mongo]
    )

    session = AgentSession(
        # vad=silero.VAD.load(),
        # stt=deepgram.STT(model="nova-3"),
        # llm=google.LLM(model="gemini-2.5-flash"),
        # tts=deepgram.TTS(),
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8
        ),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="greet the user and introduce yourself")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))