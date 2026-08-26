# D:\Admin-Module\WAI\venv\Lib\site-packages\vanna\flask\bot.py
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes
import logging

class TeamsBot(ActivityHandler):
    """
    A simple Teams bot that handles incoming messages and responds with an acknowledgment.
    This can be extended to integrate with Vanna's SQL generation logic.
    """
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Microsoft Teams.
        """
        # Log the received message
        user_message = turn_context.activity.text.strip() if turn_context.activity.text else ""
        logging.info(f"TeamsBot received message: {user_message}")

        # Send a basic response
        response_text = f"Received your message: {user_message}. Processing..."
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                text=response_text
            )
        )

    async def on_members_added_activity(self, members_added: list, turn_context: TurnContext):
        """
        Handle members added to the conversation (e.g., bot added to a channel).
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:  # Bot was added
                await turn_context.send_activity("Hello! I'm the Vanna Teams bot. Ask me anything!")