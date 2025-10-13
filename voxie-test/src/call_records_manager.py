"""
Call Records Manager - Unified Call Storage
Saves complete call transcripts and metadata to call_records table
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from supabase_client import supabase_client

logger = logging.getLogger("call-records")


class CallRecordsManager:
    """
    Manages storage of complete call records with transcripts
    
    This is separate from CallAnalytics - it stores the final,
    unified record of each call for compliance and training purposes.
    """
    
    def __init__(self):
        self.current_record_id: Optional[str] = None
        
    async def create_call_record(
        self,
        room_id: str,
        session_id: str,
        transcript_data: List[Dict[str, Any]],
        start_time: datetime,
        end_time: Optional[datetime] = None,
        call_session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
        audio_url: Optional[str] = None,
        token_usage: Optional[int] = None,
        sentiment: Optional[str] = None,
        summary: Optional[str] = None,
        call_status: str = "completed"
    ) -> Optional[str]:
        """
        Create a complete call record in the database
        
        Args:
            room_id: LiveKit room identifier
            session_id: LiveKit session identifier
            transcript_data: List of conversation turns as dicts
            start_time: When call started
            end_time: When call ended (optional, can be updated later)
            call_session_id: Link to call_sessions table (optional)
            agent_id: UUID of agent (optional)
            agent_name: Name of agent used
            customer_phone: Customer phone number
            customer_name: Customer name
            audio_url: URL to recorded audio file
            token_usage: Total tokens used
            sentiment: Overall call sentiment
            summary: Call summary text
            call_status: Status of call (completed, abandoned, error)
            
        Returns:
            UUID of created record or None if failed
        """
        try:
            # Calculate duration if end_time provided
            duration_seconds = None
            if end_time and start_time:
                duration_seconds = int((end_time - start_time).total_seconds())
            
            # Format transcript as JSONB
            transcript_jsonb = {
                "turns": transcript_data,
                "metadata": {
                    "total_turns": len(transcript_data),
                    "user_turns": sum(1 for t in transcript_data if t.get("speaker") == "user"),
                    "agent_turns": sum(1 for t in transcript_data if t.get("speaker") == "agent"),
                }
            }
            
            # Prepare record data
            record_data = {
                "room_id": room_id,
                "session_id": session_id,
                "call_session_id": call_session_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "customer_phone": customer_phone,
                "customer_name": customer_name,
                "transcript": transcript_jsonb,
                "audio_url": audio_url,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat() if end_time else None,
                "duration_seconds": duration_seconds,
                "call_status": call_status,
                "token_usage": token_usage,
                "sentiment": sentiment,
                "summary": summary
            }
            
            # Filter out None values
            record_data = {k: v for k, v in record_data.items() if v is not None}
            
            logger.info(f"💾 Creating call record for room: {room_id}")
            
            # Insert into database
            result = supabase_client.client.table('call_records').insert(record_data).execute()
            
            if result.data and len(result.data) > 0:
                record_id = result.data[0]['id']
                self.current_record_id = record_id
                logger.info(f"✅ Call record created: {record_id}")
                logger.info(f"   📝 Transcript: {len(transcript_data)} turns")
                logger.info(f"   ⏱️ Duration: {duration_seconds}s" if duration_seconds else "   ⏱️ Duration: ongoing")
                return record_id
            else:
                logger.error(f"❌ Failed to create call record - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to create call record: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def update_call_record(
        self,
        record_id: str,
        end_time: Optional[datetime] = None,
        audio_url: Optional[str] = None,
        token_usage: Optional[int] = None,
        sentiment: Optional[str] = None,
        summary: Optional[str] = None,
        call_status: Optional[str] = None
    ) -> bool:
        """
        Update an existing call record with additional data
        
        Args:
            record_id: UUID of record to update
            end_time: Call end time
            audio_url: URL to recorded audio
            token_usage: Total tokens used
            sentiment: Overall sentiment
            summary: Call summary
            call_status: Updated status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {}
            
            if end_time:
                update_data['end_time'] = end_time.isoformat()
                
                # Recalculate duration if we have start_time
                result = supabase_client.client.table('call_records')\
                    .select('start_time')\
                    .eq('id', record_id)\
                    .execute()
                
                if result.data:
                    start_time_str = result.data[0]['start_time']
                    start_time = datetime.fromisoformat(start_time_str)
                    
                    # Make sure both datetimes are timezone-aware
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)
                    
                    duration_seconds = int((end_time - start_time).total_seconds())
                    update_data['duration_seconds'] = duration_seconds
            
            if audio_url:
                update_data['audio_url'] = audio_url
            if token_usage is not None:
                update_data['token_usage'] = token_usage
            if sentiment:
                update_data['sentiment'] = sentiment
            if summary:
                update_data['summary'] = summary
            if call_status:
                update_data['call_status'] = call_status
            
            if not update_data:
                logger.warning("⚠️ No data to update")
                return False
            
            logger.info(f"🔄 Updating call record: {record_id}")
            
            supabase_client.client.table('call_records')\
                .update(update_data)\
                .eq('id', record_id)\
                .execute()
            
            logger.info(f"✅ Call record updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update call record: {e}")
            return False
    
    async def get_call_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a call record by ID"""
        try:
            result = supabase_client.client.table('call_records')\
                .select('*')\
                .eq('id', record_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get call record: {e}")
            return None
    
    async def filter_short_sessions(self, min_duration_seconds: int = 5) -> bool:
        """
        Delete call records shorter than specified duration (data cleaning)
        
        Args:
            min_duration_seconds: Minimum duration to keep (default 5s)
            
        Returns:
            True if cleanup successful
        """
        try:
            logger.info(f"🧹 Cleaning up sessions shorter than {min_duration_seconds}s")
            
            result = supabase_client.client.table('call_records')\
                .delete()\
                .lt('duration_seconds', min_duration_seconds)\
                .execute()
            
            logger.info(f"✅ Cleanup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to filter short sessions: {e}")
            return False


# ================================================================
# HELPER FUNCTIONS
# ================================================================

async def save_call_with_transcript(
    room_id: str,
    session_id: str,
    transcript_turns: List[Dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
    **kwargs
) -> Optional[str]:
    """
    Convenience function to save a complete call record
    
    Args:
        room_id: LiveKit room ID
        session_id: LiveKit session ID
        transcript_turns: List of conversation turns
        start_time: Call start time
        end_time: Call end time
        **kwargs: Additional optional fields (agent_id, summary, etc.)
        
    Returns:
        Record ID or None
    """
    manager = CallRecordsManager()
    return await manager.create_call_record(
        room_id=room_id,
        session_id=session_id,
        transcript_data=transcript_turns,
        start_time=start_time,
        end_time=end_time,
        **kwargs
    )


# ================================================================
# TESTING
# ================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_call_records():
        print("🧪 Testing Call Records Manager...\n")
        
        manager = CallRecordsManager()
        
        # Create test transcript
        test_transcript = [
            {
                "speaker": "user",
                "text": "Hello, I'd like to order a pizza",
                "timestamp": 0.5,
                "confidence": 0.98
            },
            {
                "speaker": "agent",
                "text": "Sure! What size would you like?",
                "timestamp": 2.3,
                "confidence": 1.0
            },
            {
                "speaker": "user",
                "text": "Large pepperoni please",
                "timestamp": 4.1,
                "confidence": 0.95
            }
        ]
        
        # Create call record
        record_id = await manager.create_call_record(
            room_id="test-room-123",
            session_id="test-session-456",
            transcript_data=test_transcript,
            start_time=datetime.now(timezone.utc),
            agent_name="Pizza Agent",
            customer_phone="+1234567890",
            call_status="completed"
        )
        
        if record_id:
            print(f"✅ Created record: {record_id}\n")
            
            # Update with end time and summary
            await manager.update_call_record(
                record_id=record_id,
                end_time=datetime.now(timezone.utc),
                summary="Customer ordered large pepperoni pizza",
                sentiment="positive",
                token_usage=450
            )
            
            print("✅ Updated record with end time and summary\n")
            
            # Retrieve record
            record = await manager.get_call_record(record_id)
            if record:
                print(f"✅ Retrieved record:")
                print(f"   Duration: {record['duration_seconds']}s")
                print(f"   Turns: {len(record['transcript']['turns'])}")
                print(f"   Summary: {record['summary']}")
        
        print("\n🎉 All tests passed!")
    
    asyncio.run(test_call_records())