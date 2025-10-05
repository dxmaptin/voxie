"""
Call Analytics & Token Tracking System
Integrates with LiveKit agents to track costs, quality, and conversation intelligence
"""

import uuid
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from supabase_client import supabase_client
from openai import AsyncOpenAI

logger = logging.getLogger("call-analytics")

# Initialize OpenAI client for summary generation
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class TokenUsageMetrics:
    """Token usage data from OpenAI response"""
    input_tokens: int
    output_tokens: int
    model: str
    interaction_type: str = "conversation"
    function_name: Optional[str] = None


class CallAnalytics:
    """
    Comprehensive call tracking and analytics system

    Tracks:
    - Call sessions (start/end, duration, quality)
    - Token usage and costs
    - Conversation turns and transcript
    - Call summaries and outcomes

    Usage:
        analytics = CallAnalytics(session_id="lk-session-123", agent_id="agent-uuid")
        await analytics.start_call(room_name="room-456")

        # During conversation
        await analytics.log_token_usage(...)
        await analytics.log_conversation_turn(...)

        # At end
        await analytics.end_call(rating=8)
    """

    def __init__(
        self,
        session_id: str,
        agent_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_id: Optional[str] = None
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.customer_phone = customer_phone
        self.customer_id = customer_id

        self.call_session_id: Optional[str] = None
        self.turn_number = 0
        self.total_cost_accumulated = 0.0

        # Pricing cache
        self.pricing_cache: Dict[str, Dict[str, float]] = {}
        self._load_pricing()

    def _load_pricing(self):
        """Load pricing configuration from database"""
        try:
            response = supabase_client.client.table('pricing_config')\
                .select('*')\
                .is_('effective_to', 'null')\
                .execute()

            for pricing in response.data:
                self.pricing_cache[pricing['model']] = {
                    'input': pricing['input_price_per_1m'],
                    'output': pricing['output_price_per_1m'],
                    'audio_input': pricing.get('audio_input_price_per_1m', 0),
                    'audio_output': pricing.get('audio_output_price_per_1m', 0)
                }

            logger.info(f"📊 Loaded pricing for {len(self.pricing_cache)} models")
        except Exception as e:
            logger.error(f"Failed to load pricing: {e}")
            # Fallback to hardcoded pricing
            self.pricing_cache = {
                'gpt-4o-realtime': {'input': 5.00, 'output': 20.00, 'audio_input': 100.00, 'audio_output': 200.00},
                'gpt-4o': {'input': 2.50, 'output': 10.00, 'audio_input': 0, 'audio_output': 0},
                'gpt-4o-mini': {'input': 0.15, 'output': 0.60, 'audio_input': 0, 'audio_output': 0}
            }

    async def start_call(
        self,
        room_name: str,
        primary_agent_type: Optional[str] = None,
        customer_name: Optional[str] = None
    ) -> str:
        """
        Initialize call tracking

        Returns:
            call_session_id (UUID)
        """
        try:
            # Test Supabase connection first
            print(f"🔌 DEBUG: Testing Supabase connection...")
            logger.info(f"🔌 Testing Supabase connection...")
            test_result = supabase_client.client.table('call_sessions').select('id').limit(1).execute()
            print(f"✅ DEBUG: Supabase connection working, found {len(test_result.data)} records")
            logger.info(f"✅ Supabase connection working, found {len(test_result.data)} records")

            # Insert call session
            print(f"📝 DEBUG: Inserting call session for room: {room_name}")
            logger.info(f"📝 Inserting call session for room: {room_name}")
            result = supabase_client.client.table('call_sessions').insert({
                'session_id': self.session_id,
                'room_name': room_name,
                'agent_id': self.agent_id,
                'customer_phone': self.customer_phone,
                'customer_id': self.customer_id,
                'customer_name': customer_name,
                'call_status': 'active',
                'primary_agent_type': primary_agent_type,
                'agent_transitions': [],
                'started_at': datetime.now(timezone.utc).isoformat()
            }).execute()

            print(f"🔍 DEBUG: Insert result data: {result.data}")
            if not result.data or len(result.data) == 0:
                print(f"❌ DEBUG: Insert returned no data: {result}")
                logger.error(f"❌ Insert returned no data: {result}")
                return None

            self.call_session_id = result.data[0]['id']
            print(f"📞 DEBUG: Call started: {self.call_session_id} | Room: {room_name}")
            logger.info(f"📞 Call started: {self.call_session_id} | Room: {room_name}")
            return self.call_session_id

        except Exception as e:
            print(f"❌ DEBUG EXCEPTION: {type(e).__name__}: {e}")
            logger.error(f"❌ Failed to start call tracking: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Exception details: {str(e)}")
            import traceback
            print(f"❌ DEBUG TRACEBACK: {traceback.format_exc()}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None

    async def log_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        interaction_type: str = 'conversation',
        function_name: Optional[str] = None,
        agent_state: Optional[str] = None,
        input_audio_tokens: int = 0,
        output_audio_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Log token usage and calculate cost

        Returns:
            Cost breakdown: {'input_cost', 'output_cost', 'total_cost'}
        """
        if not self.call_session_id:
            logger.warning("⚠️ Cannot log tokens - call not started")
            return {'input_cost': 0, 'output_cost': 0, 'total_cost': 0}

        try:
            # Get pricing for model
            pricing = self.pricing_cache.get(model)
            if not pricing:
                logger.warning(f"⚠️ No pricing for model {model}, using default")
                pricing = self.pricing_cache.get('gpt-4o-realtime', {'input': 5.00, 'output': 20.00})

            # Calculate costs
            input_cost = (input_tokens / 1_000_000) * pricing['input']
            output_cost = (output_tokens / 1_000_000) * pricing['output']

            # Add audio costs if applicable
            if input_audio_tokens > 0:
                input_cost += (input_audio_tokens / 1_000_000) * pricing.get('audio_input', 0)
            if output_audio_tokens > 0:
                output_cost += (output_audio_tokens / 1_000_000) * pricing.get('audio_output', 0)

            total_cost = input_cost + output_cost
            self.total_cost_accumulated += total_cost

            # Insert into database
            supabase_client.client.table('token_usage').insert({
                'call_session_id': self.call_session_id,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'input_audio_tokens': input_audio_tokens,
                'output_audio_tokens': output_audio_tokens,
                'input_cost_usd': round(input_cost, 6),
                'output_cost_usd': round(output_cost, 6),
                'interaction_type': interaction_type,
                'function_name': function_name,
                'agent_state': agent_state,
                'recorded_at': datetime.now(timezone.utc).isoformat()
            }).execute()

            logger.info(
                f"💰 Tokens: {input_tokens + output_tokens} "
                f"| Cost: ${total_cost:.4f} "
                f"| Type: {interaction_type} "
                f"| Total: ${self.total_cost_accumulated:.4f}"
            )

            return {
                'input_cost': round(input_cost, 6),
                'output_cost': round(output_cost, 6),
                'total_cost': round(total_cost, 6)
            }

        except Exception as e:
            logger.error(f"❌ Failed to log token usage: {e}")
            return {'input_cost': 0, 'output_cost': 0, 'total_cost': 0}

    async def log_conversation_turn(
        self,
        speaker: str,  # 'user' or 'agent'
        transcript: str,
        agent_name: Optional[str] = None,
        audio_duration_ms: Optional[int] = None,
        intent: Optional[str] = None,
        sentiment: Optional[str] = None,
        entities: Optional[Dict] = None,
        function_called: Optional[str] = None,
        function_params: Optional[Dict] = None,
        function_result: Optional[Dict] = None
    ):
        """Log a conversation turn with optional analysis"""
        if not self.call_session_id:
            logger.warning("⚠️ Cannot log turn - call not started")
            return

        try:
            self.turn_number += 1

            supabase_client.client.table('conversation_turns').insert({
                'call_session_id': self.call_session_id,
                'turn_number': self.turn_number,
                'speaker': speaker,
                'agent_name': agent_name,
                'transcript': transcript,
                'audio_duration_ms': audio_duration_ms,
                'intent': intent,
                'sentiment': sentiment,
                'entities': entities or {},
                'function_called': function_called,
                'function_params': function_params,
                'function_result': function_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }).execute()

            logger.debug(f"📝 Turn {self.turn_number}: {speaker} - {transcript[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to log conversation turn: {e}")

    async def log_agent_transition(
        self,
        from_agent: str,
        to_agent: str,
        reason: Optional[str] = None
    ):
        """Log when call is handed off between agents"""
        if not self.call_session_id:
            return

        try:
            # Get current transitions
            result = supabase_client.client.table('call_sessions')\
                .select('agent_transitions')\
                .eq('id', self.call_session_id)\
                .execute()

            transitions = result.data[0]['agent_transitions'] or []
            transitions.append({
                'from': from_agent,
                'to': to_agent,
                'at': datetime.now(timezone.utc).isoformat(),
                'reason': reason
            })

            # Update
            supabase_client.client.table('call_sessions')\
                .update({'agent_transitions': transitions})\
                .eq('id', self.call_session_id)\
                .execute()

            logger.info(f"🔄 Agent transition: {from_agent} → {to_agent}")

        except Exception as e:
            logger.error(f"❌ Failed to log agent transition: {e}")

    async def end_call(
        self,
        call_status: str = 'completed',
        rating: Optional[int] = None,
        rating_reason: Optional[str] = None,
        sentiment: Optional[str] = None,
        issue_resolved: Optional[bool] = None
    ):
        """Mark call as ended and update metrics"""
        if not self.call_session_id:
            logger.warning("⚠️ Cannot end call - not started")
            return

        try:
            supabase_client.client.table('call_sessions').update({
                'ended_at': datetime.now(timezone.utc).isoformat(),
                'call_status': call_status,
                'call_rating': rating,
                'call_rating_reason': rating_reason,
                'customer_sentiment': sentiment,
                'issue_resolved': issue_resolved
            }).eq('id', self.call_session_id).execute()

            logger.info(
                f"📞 Call ended: {call_status} "
                f"| Rating: {rating or 'N/A'} "
                f"| Total Cost: ${self.total_cost_accumulated:.4f}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to end call: {e}")

    async def auto_generate_summary(self) -> Optional[Dict[str, Any]]:
        """
        Automatically generate call summary using GPT-4o
        Fetches conversation transcript and generates comprehensive summary

        Returns:
            Summary data dict or None if failed
        """
        if not self.call_session_id:
            logger.warning("⚠️ Cannot generate summary - call not started")
            return None

        try:
            # Fetch conversation turns from database
            result = supabase_client.client.table('conversation_turns')\
                .select('turn_number, speaker, transcript, agent_name')\
                .eq('call_session_id', self.call_session_id)\
                .order('turn_number')\
                .execute()

            if not result.data or len(result.data) == 0:
                logger.warning("⚠️ No conversation turns found for summary")
                return None

            # Build transcript
            transcript_lines = []
            for turn in result.data:
                speaker_name = turn.get('agent_name', 'Agent') if turn['speaker'] == 'agent' else 'User'
                transcript_lines.append(f"{speaker_name}: {turn['transcript']}")

            full_transcript = "\n".join(transcript_lines)

            # Generate summary using GPT-4o
            logger.info("🤖 Generating call summary with GPT-4o...")

            prompt = f"""Analyze this customer service call transcript and provide a structured summary.

TRANSCRIPT:
{full_transcript}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise 2-3 sentence overview of the call",
    "key_points": ["point 1", "point 2", "point 3"],
    "action_items": ["action 1", "action 2"],
    "call_category": "new_order|support|inquiry|complaint|booking",
    "business_outcome": "sale|lead|resolution|escalation|no_outcome",
    "sentiment": "positive|neutral|negative|mixed",
    "sales_value": null or number (if a sale was made)
}}

Only respond with valid JSON, no other text."""

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a call analytics assistant. Analyze call transcripts and provide structured summaries in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse response
            import json
            summary_data = json.loads(response.choices[0].message.content)
            tokens_used = response.usage.total_tokens

            # Store summary in database
            supabase_client.client.table('call_summaries').insert({
                'call_session_id': self.call_session_id,
                'summary_text': summary_data.get('summary', ''),
                'key_points': summary_data.get('key_points', []),
                'action_items': summary_data.get('action_items', []),
                'call_category': summary_data.get('call_category'),
                'business_outcome': summary_data.get('business_outcome'),
                'sales_value_usd': summary_data.get('sales_value'),
                'tokens_used': tokens_used,
                'generated_by': 'gpt-4o',
                'generated_at': datetime.now(timezone.utc).isoformat()
            }).execute()

            # Also update call_sessions with sentiment
            if summary_data.get('sentiment'):
                supabase_client.client.table('call_sessions')\
                    .update({'customer_sentiment': summary_data['sentiment']})\
                    .eq('id', self.call_session_id)\
                    .execute()

            logger.info(
                f"✅ Summary generated | Category: {summary_data.get('call_category')} | "
                f"Outcome: {summary_data.get('business_outcome')} | Tokens: {tokens_used}"
            )

            # Log the summary generation cost
            await self.log_token_usage(
                model='gpt-4o',
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                interaction_type='processing',
                agent_state='summary_generation'
            )

            return summary_data

        except Exception as e:
            logger.error(f"❌ Failed to auto-generate summary: {e}")
            return None

    async def generate_summary(
        self,
        summary_text: str,
        key_points: List[str] = None,
        action_items: List[str] = None,
        call_category: Optional[str] = None,
        business_outcome: Optional[str] = None,
        sales_value_usd: Optional[float] = None,
        tokens_used: Optional[int] = None
    ):
        """
        Manually store a pre-generated call summary
        (Use auto_generate_summary() for automatic AI-generated summaries)
        """
        if not self.call_session_id:
            return

        try:
            supabase_client.client.table('call_summaries').insert({
                'call_session_id': self.call_session_id,
                'summary_text': summary_text,
                'key_points': key_points or [],
                'action_items': action_items or [],
                'call_category': call_category,
                'business_outcome': business_outcome,
                'sales_value_usd': sales_value_usd,
                'tokens_used': tokens_used,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }).execute()

            logger.info(f"📋 Summary generated: {call_category or 'uncategorized'}")

        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {e}")

    async def update_quality_metrics(
        self,
        audio_quality_score: Optional[float] = None,
        latency_avg_ms: Optional[int] = None,
        error_count: Optional[int] = None
    ):
        """Update technical quality metrics"""
        if not self.call_session_id:
            return

        try:
            update_data = {}
            if audio_quality_score is not None:
                update_data['audio_quality_score'] = audio_quality_score
            if latency_avg_ms is not None:
                update_data['latency_avg_ms'] = latency_avg_ms
            if error_count is not None:
                update_data['errors_count'] = error_count

            if update_data:
                supabase_client.client.table('call_sessions')\
                    .update(update_data)\
                    .eq('id', self.call_session_id)\
                    .execute()

        except Exception as e:
            logger.error(f"❌ Failed to update quality metrics: {e}")


# ================================================================
# HELPER FUNCTIONS
# ================================================================

async def get_call_cost(session_id: str) -> Dict[str, Any]:
    """Get total cost for a call session"""
    try:
        result = supabase_client.client.table('token_usage')\
            .select('*')\
            .eq('call_session_id', session_id)\
            .execute()

        total_tokens = sum(row['total_tokens'] for row in result.data)
        total_cost = sum(row['total_cost_usd'] for row in result.data)

        return {
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'breakdown': result.data
        }
    except Exception as e:
        logger.error(f"Failed to get call cost: {e}")
        return {'total_tokens': 0, 'total_cost_usd': 0, 'breakdown': []}


async def get_daily_stats(date: Optional[datetime] = None) -> Dict[str, Any]:
    """Get statistics for a specific day"""
    if not date:
        date = datetime.now(timezone.utc)

    try:
        # Use the pre-built view
        result = supabase_client.client.table('daily_cost_summary')\
            .select('*')\
            .eq('date', date.date())\
            .execute()

        if result.data:
            return result.data[0]
        return {}
    except Exception as e:
        logger.error(f"Failed to get daily stats: {e}")
        return {}


async def get_agent_performance(agent_id: str, days: int = 30) -> Dict[str, Any]:
    """Get performance metrics for a specific agent"""
    try:
        # Use the pre-built view
        result = supabase_client.client.rpc('get_agent_performance', {
            'agent_id_param': agent_id,
            'days_param': days
        }).execute()

        return result.data[0] if result.data else {}
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        return {}


# ================================================================
# TESTING
# ================================================================

if __name__ == "__main__":
    import asyncio

    async def test_analytics():
        print("🧪 Testing Call Analytics System...\n")

        # Start a test call
        analytics = CallAnalytics(
            session_id="test-session-" + str(uuid.uuid4()),
            agent_id=None,  # Will use first agent in DB
            customer_phone="+1234567890"
        )

        call_id = await analytics.start_call(
            room_name="test-room-123",
            primary_agent_type="test",
            customer_name="Test Customer"
        )

        print(f"✅ Call started: {call_id}\n")

        # Log some token usage
        cost = await analytics.log_token_usage(
            model="gpt-4o-realtime",
            input_tokens=150,
            output_tokens=300,
            interaction_type="conversation"
        )
        print(f"✅ Logged tokens: ${cost['total_cost']:.4f}\n")

        # Log conversation turns
        await analytics.log_conversation_turn(
            speaker="user",
            transcript="I want to order a pizza",
            intent="new_order",
            sentiment="neutral"
        )

        await analytics.log_conversation_turn(
            speaker="agent",
            transcript="Sure! What size would you like?",
            agent_name="Pizza Agent",
            sentiment="positive"
        )

        print("✅ Logged 2 conversation turns\n")

        # End call
        await analytics.end_call(
            rating=9,
            rating_reason="Fast and helpful",
            sentiment="positive",
            issue_resolved=True
        )

        print("✅ Call ended\n")

        # Auto-generate summary using GPT-4o
        print("🤖 Auto-generating call summary with GPT-4o...\n")
        summary = await analytics.auto_generate_summary()

        if summary:
            print("✅ Summary generated automatically!")
            print(f"   Category: {summary.get('call_category')}")
            print(f"   Outcome: {summary.get('business_outcome')}")
            print(f"   Summary: {summary.get('summary')}")
        else:
            print("⚠️ Summary generation skipped (no conversation turns or error)")

        print(f"\n💰 Total cost for call: ${analytics.total_cost_accumulated:.4f}")
        print("\n🎉 All tests passed!")

    asyncio.run(test_analytics())
