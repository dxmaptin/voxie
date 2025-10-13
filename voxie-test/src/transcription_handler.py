"""
Transcription Handler - Parallel STT for Speech-to-Speech Analytics
Transcribes user and agent audio in parallel without affecting latency
Accumulates transcript in memory for end-of-call summary generation
"""

import logging
import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import tiktoken

logger = logging.getLogger("transcription")


@dataclass
class TranscriptTurn:
    """Single turn in the conversation"""
    speaker: str  # 'user' or 'agent'
    text: str
    timestamp: float
    confidence: float = 1.0


class TranscriptionHandler:
    """
    Handles parallel transcription of speech-to-speech conversations

    Features:
    - Transcribes user and agent audio in parallel
    - Accumulates full transcript in memory (not DB)
    - Estimates tokens using tiktoken
    - Generates summary at call end only
    """

    def __init__(self, analytics=None):
        """
        Initialize transcription handler

        Args:
            analytics: CallAnalytics instance for logging
        """
        self.analytics = analytics
        self.full_transcript: List[TranscriptTurn] = []
        self.total_input_tokens_estimate = 0
        self.total_output_tokens_estimate = 0
        self.call_start_time = time.time()

        # Initialize tiktoken for token estimation
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
            logger.info("✅ Tiktoken initialized for gpt-4o")
        except Exception as e:
            logger.warning(f"⚠️ Failed to init tiktoken: {e}, using fallback")
            self.tokenizer = None

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text

        Args:
            text: Text to tokenize

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Tokenizer error: {e}, using fallback")

        # Fallback: rough estimation (words × 1.3)
        words = len(text.split())
        return int(words * 1.3)

    async def on_user_speech(self, transcript_text: str, confidence: float = 1.0):
        """
        Handle user speech transcription

        Args:
            transcript_text: Transcribed text from STT (or user input in console mode)
            confidence: Transcription confidence score
        """
        if not transcript_text or transcript_text.strip() == "":
            return

        # Clean up transcript
        transcript_text = transcript_text.strip()

        # Estimate tokens
        tokens = self.estimate_tokens(transcript_text)
        self.total_input_tokens_estimate += tokens

        # Store in memory
        turn = TranscriptTurn(
            speaker='user',
            text=transcript_text,
            timestamp=time.time() - self.call_start_time,
            confidence=confidence
        )
        self.full_transcript.append(turn)

        logger.info(f"👤 User ({tokens} tokens): {transcript_text[:80]}...")

    async def on_agent_speech(self, transcript_text: str, confidence: float = 1.0):
        """
        Handle agent speech transcription

        Args:
            transcript_text: Transcribed text from STT (or agent output in console mode)
            confidence: Transcription confidence score
        """
        if not transcript_text or transcript_text.strip() == "":
            return

        # Clean up transcript
        transcript_text = transcript_text.strip()

        # Estimate tokens
        tokens = self.estimate_tokens(transcript_text)
        self.total_output_tokens_estimate += tokens

        # Store in memory
        turn = TranscriptTurn(
            speaker='agent',
            text=transcript_text,
            timestamp=time.time() - self.call_start_time,
            confidence=confidence
        )
        self.full_transcript.append(turn)

        logger.info(f"🤖 Agent ({tokens} tokens): {transcript_text[:80]}...")

    def get_full_conversation_text(self) -> str:
        """
        Build full conversation as formatted text

        Returns:
            Formatted conversation string
        """
        lines = []
        for turn in self.full_transcript:
            speaker_label = "User" if turn.speaker == 'user' else "Agent"
            lines.append(f"{speaker_label}: {turn.text}")

        return "\n".join(lines)

    async def generate_summary_and_log(self):
        """
        Generate summary from full transcript and log to analytics
        Called at end of call only
        """
        if not self.analytics:
            logger.warning("⚠️ No analytics instance, skipping summary")
            return None

        if len(self.full_transcript) == 0:
            logger.warning("⚠️ No transcript to summarize")
            return None

        try:
            # Log estimated token usage for the entire call
            logger.info(f"📊 Estimated tokens - Input: {self.total_input_tokens_estimate}, Output: {self.total_output_tokens_estimate}")

            await self.analytics.log_token_usage(
                model='gpt-4o-realtime',
                input_tokens=self.total_input_tokens_estimate,
                output_tokens=self.total_output_tokens_estimate,
                interaction_type='conversation',
                agent_state='realtime_conversation'
            )

            # Get full conversation text
            conversation_text = self.get_full_conversation_text()

            logger.info(f"📝 Full transcript ({len(self.full_transcript)} turns, {len(conversation_text)} chars)")
            logger.info(f"🤖 Generating summary from transcript...")

            # Generate summary using GPT-4o
            summary_data = await self._generate_summary_with_gpt4o(conversation_text)

            if summary_data:
                logger.info(f"✅ Summary generated: {summary_data.get('call_category')} - {summary_data.get('business_outcome')}")
                return summary_data
            else:
                logger.warning("⚠️ Summary generation failed")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {e}")
            return None

    async def _generate_summary_with_gpt4o(self, conversation_text: str) -> Optional[Dict]:
        """
        Generate summary using GPT-4o (reuses logic from CallAnalytics)

        Args:
            conversation_text: Full conversation transcript

        Returns:
            Summary data dict or None
        """
        if not self.analytics:
            return None

        try:
            from openai import AsyncOpenAI
            import json

            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = f"""Analyze this customer service call transcript and provide a structured summary.

TRANSCRIPT:
{conversation_text}

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
            summary_data = json.loads(response.choices[0].message.content)
            tokens_used = response.usage.total_tokens

            # Store summary in database using CallAnalytics
            await self.analytics.generate_summary(
                summary_text=summary_data.get('summary', ''),
                key_points=summary_data.get('key_points', []),
                action_items=summary_data.get('action_items', []),
                call_category=summary_data.get('call_category'),
                business_outcome=summary_data.get('business_outcome'),
                sales_value_usd=summary_data.get('sales_value'),
                tokens_used=tokens_used
            )

            # Log summary generation cost
            await self.analytics.log_token_usage(
                model='gpt-4o',
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                interaction_type='processing',
                agent_state='summary_generation'
            )

            return summary_data

        except Exception as e:
            logger.error(f"❌ Failed to generate summary with GPT-4o: {e}")
            return None

    def get_stats(self) -> Dict:
        """Get statistics about the transcript"""
        return {
            'total_turns': len(self.full_transcript),
            'user_turns': sum(1 for t in self.full_transcript if t.speaker == 'user'),
            'agent_turns': sum(1 for t in self.full_transcript if t.speaker == 'agent'),
            'estimated_input_tokens': self.total_input_tokens_estimate,
            'estimated_output_tokens': self.total_output_tokens_estimate,
            'estimated_total_tokens': self.total_input_tokens_estimate + self.total_output_tokens_estimate,
            'call_duration_seconds': time.time() - self.call_start_time
        }
    
    async def save_to_call_records(
        self,
        room_id: str,
        session_id: str,
        call_session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        start_time: Optional[float] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Save full transcript to call_records table
        
        Args:
            room_id: LiveKit room ID
            session_id: LiveKit session ID
            call_session_id: Link to call_sessions table
            agent_name: Name of agent used
            start_time: Call start timestamp (uses self.call_start_time if not provided)
            **kwargs: Additional fields (customer_phone, sentiment, etc.)
            
        Returns:
            Record ID or None
        """
        if len(self.full_transcript) == 0:
            logger.warning("⚠️ No transcript to save")
            return None
        
        try:
            from call_records_manager import CallRecordsManager
            from datetime import datetime, timezone
            
            # Convert transcript to dict format
            transcript_turns = [
                {
                    "speaker": turn.speaker,
                    "text": turn.text,
                    "timestamp": turn.timestamp,
                    "confidence": turn.confidence
                }
                for turn in self.full_transcript
            ]
            
            # Calculate times
            call_start = datetime.fromtimestamp(
                start_time if start_time else self.call_start_time,
                tz=timezone.utc
            )
            call_end = datetime.now(timezone.utc)
            
            # Create manager and save
            manager = CallRecordsManager()
            record_id = await manager.create_call_record(
                room_id=room_id,
                session_id=session_id,
                transcript_data=transcript_turns,
                start_time=call_start,
                end_time=call_end,
                call_session_id=call_session_id,
                agent_name=agent_name,
                token_usage=self.total_input_tokens_estimate + self.total_output_tokens_estimate,
                **kwargs
            )
            
            if record_id:
                logger.info(f"✅ Transcript saved to call_records: {record_id}")
            
            return record_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save transcript to call_records: {e}")
            return None
