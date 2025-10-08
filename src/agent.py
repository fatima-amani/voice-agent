from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
    BackgroundAudioPlayer,
    BuiltinAudioClip,
    AudioConfig
)
from livekit.plugins import google, anam

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

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = Agent(
        instructions=get_agent_instruction(),
        tools=[neo4j, mongo]
    )

    session = AgentSession(
        preemptive_generation=True,
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Aoede", # Sulafat Despina Aoede
            temperature=0.8
        ),
    )

    avatar = anam.AvatarSession(
      persona_config=anam.PersonaConfig(
         name="Cara",  # Name of the avatar to use.
         avatarId="d9ebe82e-2f34-4ff6-9632-16cb73e7de08"  # ID of the avatar to use. See "Avatar setup" for details.
      ),
    )

    # Start the avatar and wait for it to join
    await avatar.start(session, room=ctx.room)

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="greet the user and introduce yourself")

    background_audio = BackgroundAudioPlayer(
        # play office ambience sound looping in the background
        ambient_sound=AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=0.8),
        # play keyboard typing sound when the agent is thinking
        thinking_sound=[
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8),
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7),
        ],
    )

    await background_audio.start(room=ctx.room, agent_session=session)

    # Play another audio file at any time using the play method:
    # background_audio.play("filepath.ogg")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))