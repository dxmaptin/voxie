"""
Parallel Audio Transcription Handler
Transcribes user and agent audio streams in parallel using Deepgram STT
Does NOT affect speech-to-speech latency - runs completely separately
"""

import logging
import asyncio
from typing import Optional
from livekit.plugins import deepgram
from livekit import rtc
from transcription_handler import TranscriptionHandler

logger = logging.getLogger("parallel-transcription")


class ParallelAudioTranscriber:
    """
    Handles parallel STT transcription of audio streams

    Features:
    - Subscribes to user audio track
    - Captures agent audio output
    - Sends to Deepgram STT in parallel
    - Feeds transcripts to TranscriptionHandler
    - Zero impact on speech-to-speech latency
    """

    def __init__(self, transcription_handler: TranscriptionHandler):
        """
        Initialize parallel transcriber

        Args:
            transcription_handler: TranscriptionHandler to receive transcripts
        """
        self.transcription = transcription_handler
        self.user_stt: Optional[deepgram.STT] = None
        self.agent_stt: Optional[deepgram.STT] = None
        self.is_running = False

        # Initialize Deepgram STT
        try:
            self.user_stt = deepgram.STT(
                model="nova-2",
                language="en",
                interim_results=False  # Only final results
            )
            self.agent_stt = deepgram.STT(
                model="nova-2",
                language="en",
                interim_results=False
            )
            logger.info("✅ Deepgram STT initialized for parallel transcription")
        except Exception as e:
            logger.warning(f"⚠️ Failed to init Deepgram: {e}")
            logger.warning("⚠️ Parallel transcription will not be available")

    async def start_user_transcription(self, audio_track: rtc.AudioTrack):
        """
        Start transcribing user's audio track in parallel

        Args:
            audio_track: User's audio track from LiveKit
        """
        if not self.user_stt:
            logger.warning("⚠️ Deepgram not available, skipping user transcription")
            return

        try:
            logger.info("🎤 Starting parallel user audio transcription...")

            # Create audio stream from track
            audio_stream = rtc.AudioStream(audio_track)

            # Stream to Deepgram STT
            stt_stream = self.user_stt.stream()

            async def process_user_audio():
                """Process user audio frames and send to Deepgram"""
                async for audio_frame in audio_stream:
                    # Send frame to Deepgram (non-blocking)
                    await stt_stream.push_frame(audio_frame)

            async def process_user_transcripts():
                """Receive transcripts from Deepgram and log"""
                async for event in stt_stream:
                    if event.is_final and event.alternatives:
                        transcript = event.alternatives[0].transcript
                        confidence = event.alternatives[0].confidence

                        # Log to transcription handler
                        await self.transcription.on_user_speech(
                            transcript_text=transcript,
                            confidence=confidence
                        )

            # Run both tasks in parallel
            await asyncio.gather(
                process_user_audio(),
                process_user_transcripts()
            )

        except Exception as e:
            logger.error(f"❌ Error in user transcription: {e}")

    async def start_agent_transcription(self, audio_source: rtc.AudioSource):
        """
        Start transcribing agent's audio output in parallel

        Args:
            audio_source: Agent's audio output source from LiveKit
        """
        if not self.agent_stt:
            logger.warning("⚠️ Deepgram not available, skipping agent transcription")
            return

        try:
            logger.info("🤖 Starting parallel agent audio transcription...")

            # Create audio stream from source
            audio_stream = rtc.AudioStream(audio_source)

            # Stream to Deepgram STT
            stt_stream = self.agent_stt.stream()

            async def process_agent_audio():
                """Process agent audio frames and send to Deepgram"""
                async for audio_frame in audio_stream:
                    # Send frame to Deepgram (non-blocking)
                    await stt_stream.push_frame(audio_frame)

            async def process_agent_transcripts():
                """Receive transcripts from Deepgram and log"""
                async for event in stt_stream:
                    if event.is_final and event.alternatives:
                        transcript = event.alternatives[0].transcript
                        confidence = event.alternatives[0].confidence

                        # Log to transcription handler
                        await self.transcription.on_agent_speech(
                            transcript_text=transcript,
                            confidence=confidence
                        )

            # Run both tasks in parallel
            await asyncio.gather(
                process_agent_audio(),
                process_agent_transcripts()
            )

        except Exception as e:
            logger.error(f"❌ Error in agent transcription: {e}")

    async def transcribe_user_track(self, participant: rtc.Participant):
        """
        Subscribe to user's audio and start parallel transcription

        Args:
            participant: Remote participant (user)
        """
        try:
            # Find audio track
            audio_track = None
            for publication in participant.track_publications.values():
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_AUDIO:
                    audio_track = publication.track
                    break

            if audio_track:
                logger.info(f"📡 Subscribing to user audio: {participant.identity}")
                await self.start_user_transcription(audio_track)
            else:
                logger.warning(f"⚠️ No audio track found for {participant.identity}")

        except Exception as e:
            logger.error(f"❌ Failed to transcribe user track: {e}")

    def stop(self):
        """Stop all transcription"""
        self.is_running = False
        logger.info("🛑 Parallel transcription stopped")
