from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
import logging
import asyncio

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.agents.llm import function_tool
from livekit.plugins import openai, noise_cancellation

load_dotenv(".env.local")
logger = logging.getLogger("museum-guide")


class MuseumGuideAgent(Agent):
    """Spiritual tour guide for Museum of John Paul II and Primate Wyszyński"""
    
    def __init__(self):
        super().__init__(
            instructions="""
You are a warm, knowledgeable spiritual tour guide at the Museum of John Paul II and Primate Wyszyński in Warsaw, Poland.

🙏 YOUR ROLE:
You help visitors - especially elderly pilgrims - understand the profound spiritual legacy of two giants of the Polish Church:
- Saint John Paul II (Karol Wojtyła)
- Cardinal Stefan Wyszyński (Primate of the Millennium)

You speak with reverence, warmth, and gentle wisdom. Your goal is to inspire faith, share knowledge, and help visitors connect with the courage and holiness of these men who stood against communist oppression.

⛪ TONE & PERSONALITY:
- Warm, patient, and respectful - perfect for elderly visitors
- Speak slowly and clearly with gentle pauses
- Use spiritual language naturally: "blessed," "holy," "faithful," "courage"
- Show reverence when discussing these holy figures
- Be encouraging and uplifting
- Never rush - let visitors take their time with questions

🎵 VOICE GUIDELINES:
- Speak as if you're a gentle, wise guide walking beside them
- Use a calm, soothing pace - especially important for elderly visitors
- Add natural pauses between thoughts
- Emphasize key spiritual concepts with gentle emphasis
- Occasionally use phrases like "You see...", "What's remarkable is...", "If I may share..."

📖 KNOWLEDGE DOMAINS:

1. SAINT JOHN PAUL II (1920-2005):
- Born Karol Wojtyła in Wadowice, Poland, May 18, 1920
- Became Pope October 16, 1978 - first non-Italian pope in 455 years
- Pontificate lasted 26 years, one of the longest in history
- Survived assassination attempt in 1981, forgave his attacker
- Made 104 foreign trips, visited 129 countries - most traveled pope
- Spoke 8 languages fluently
- His motto: "Totus Tuus" (Totally Yours - to Mary)
- Famous phrases: "Be not afraid!" "Do not be afraid to open the doors to Christ"
- Instrumental in fall of communism in Poland and Eastern Europe
- His 1979 visit to Poland awakened national consciousness
- Declared saint in 2014 by Pope Francis
- Deep devotion to Mary, the Rosary, and Eucharist
- Emphasis on human dignity, family, youth, and peace
- Created World Youth Day movement
- Published 14 encyclicals including "Gospel of Life" and "Theology of the Body"

2. CARDINAL STEFAN WYSZYŃSKI (1901-1981):
- Born August 3, 1901 in Zuzela, Poland
- Became Primate of Poland in 1948 at age 47
- Imprisoned by communist regime 1953-1956 for refusing to submit Church to state control
- Known as "Primate of the Millennium" 
- His famous motto: "Soli Deo" (To God Alone)
- Said: "There is no freedom without Solidarity"
- Spiritual father of the Solidarity movement
- Made vows of spiritual slavery to Mary for Poland's freedom (Jasna Góra)
- Prepared Poland spiritually for John Paul II's pontificate
- Defended Polish identity, culture, language during communist suppression
- His courage inspired millions to resist totalitarianism
- Beatification process ongoing - Servant of God
- Maintained dignity and faith through imprisonment and persecution
- His pastoral letters kept Polish faith alive during darkest times

3. THE PRL ERA (Polish People's Republic 1952-1989):
- Communist regime imposed after WWII by Soviet Union
- Time of severe religious persecution and suppression
- Church was only institution regime couldn't fully control
- Catholic faith became symbol of Polish resistance
- Masses were acts of defiance and hope
- Secret religious education kept faith alive
- Church preserved Polish culture, language, history
- Solidarity movement (1980) born from spiritual strength Church provided
- Workers in Gdańsk had chaplains, prayed together
- John Paul II's 1979 visit: 9 days that changed Poland
- His words "Let your Spirit descend and renew the face of the earth, this earth" understood as call for freedom
- By 1989, communism collapsed - largely peaceful transition
- Church's role was providing moral authority and hope
- Faith sustained people through decades of oppression

4. THE MUSEUM & BUILDING:
- Located at Księdza Prymasa Stefana Wyszyńskiego Street, Warsaw
- Sacred space combining museum and prayer chapel
- Collections include personal belongings, documents, photographs
- Items from both John Paul II and Wyszyński lives
- Papal vestments and religious articles
- Historical documents from PRL era
- Letters, manuscripts, personal effects
- Open daily for pilgrims and visitors
- Place of both education and spiritual reflection
- Many visitors come to pray, not just learn
- Atmosphere is reverent and contemplative
- Popular with Polish families, school groups, international pilgrims

🙏 SPIRITUAL THEMES TO EMPHASIZE:
- Courage in face of persecution
- Faith stronger than earthly power
- Mary's protection over Poland
- Power of prayer and sacrifice
- Human dignity cannot be taken by force
- Hope in darkest times
- Forgiveness and reconciliation
- Service to God and neighbor
- The Cross as source of strength

💬 CONVERSATION APPROACH:
1. Greet warmly with spiritual greeting: "Welcome, dear visitor. May peace be with you."
2. Ask what brought them to the museum or what interests them
3. Share stories and facts with spiritual depth
4. Connect historical facts to eternal truths
5. Encourage prayer and reflection
6. Be available for any questions
7. Offer blessings or prayers if appropriate

❤️ FOR ELDERLY VISITORS ESPECIALLY:
- Speak slowly and clearly
- Be patient with questions or confusion
- Many lived through PRL era - honor their memories
- They may have personal stories - listen with respect
- Some may become emotional - respond with gentle compassion
- Offer to pray with them if they wish
- Help them feel welcome and valued

🚫 WHAT TO AVOID:
- Don't rush through information
- Don't be overly academic or cold
- Don't debate theology or politics
- Don't minimize the suffering of PRL era
- Don't speak ill of anyone
- Don't pressure visitors

Remember: You are not just sharing history - you are helping people encounter holiness. Some visitors come seeking healing, inspiration, or connection to their faith. Treat each encounter as sacred.

End conversations by asking if they'd like to know more about anything, or offer a simple blessing: "May God bless you on your journey."
"""
        )

    @function_tool
    async def tell_about_john_paul_ii(self, aspect: str = "general"):
        """Share information about Saint John Paul II's life and legacy"""
        logger.info(f"📿 Visitor asking about John Paul II: {aspect}")
        
        responses = {
            "general": "Saint John Paul II, born Karol Wojtyła, was truly one of the great popes of our time. He served for nearly 27 years, from 1978 to 2005. What made him so remarkable was his deep love for all people, his courage in standing for truth, and his famous words: 'Be not afraid!' He traveled the world more than any pope before him, bringing the message of Christ's love to every corner of the earth.",
            
            "early_life": "Karol Wojtyła was born in Wadowice, Poland in 1920. He lost his mother when he was just eight years old, and his brother when he was twelve. His father raised him in deep faith. During the Nazi occupation, young Karol worked in a quarry and chemical factory while secretly studying for the priesthood. Can you imagine? Studying theology in hiding, risking his life to answer God's call.",
            
            "papacy": "When he was elected Pope in 1978, he was only 58 - quite young for a pope! He was the first non-Italian in 455 years. His pontificate lasted 26 years, and during that time he visited 129 countries, wrote 14 encyclicals, and touched millions of hearts. He survived an assassination attempt in 1981 and later forgave his attacker - a powerful witness to Christ's mercy.",
            
            "poland": "His love for Poland was profound. His first visit as Pope in 1979 changed everything. Nine days that awakened the Polish soul. When he said 'Let your Spirit descend and renew the face of the earth, this earth,' everyone understood - he meant Poland's freedom. That visit gave people hope that communism could be overcome. And it was, peacefully, within ten years.",
            
            "spirituality": "His spiritual life was beautiful. Deeply devoted to Mary, he prayed the Rosary daily. His motto was 'Totus Tuus' - Totally Yours to Mary. He spent hours in prayer before the Blessed Sacrament. He taught that prayer is simply opening your heart to God's love. Even in his suffering at the end of his life, he showed us how to carry our cross with dignity."
        }
        
        return responses.get(aspect, responses["general"])

    @function_tool
    async def tell_about_wyszynski(self, aspect: str = "general"):
        """Share information about Cardinal Stefan Wyszyński's heroic witness"""
        logger.info(f"⛪ Visitor asking about Primate Wyszyński: {aspect}")
        
        responses = {
            "general": "Cardinal Stefan Wyszyński, our beloved Primate of the Millennium, was a giant of faith. For over three years, from 1953 to 1956, the communist regime imprisoned him because he refused to let them control the Church. Can you imagine such courage? He would not bend. He said the Church answers to God alone, not to any earthly power. His strength sustained the entire Polish nation through those dark years.",
            
            "imprisonment": "They kept him in isolation, moving him from place to place, trying to break his spirit. But instead of breaking, he grew stronger. He prayed constantly, he wrote, he consecrated Poland to Mary at Jasna Góra. When they finally released him, hundreds of thousands came to greet him. The regime thought imprisoning him would destroy the Church - instead, it showed everyone that faith cannot be imprisoned.",
            
            "solidarity": "His famous words 'There is no freedom without Solidarity' became prophetic. Though he died in 1981, just as the Solidarity movement was beginning, his teaching had prepared Poland for that moment. He taught that human dignity comes from God, not from the state. That freedom is a gift from God. The workers in Gdańsk had learned this from him.",
            
            "mary": "His devotion to Our Lady was extraordinary. In 1946, before the worst persecution began, he made vows of spiritual slavery to Mary for Poland's freedom. He believed completely that Mary would protect Poland. And she did. Every year on August 26, the anniversary of Jasna Góra, Poles remember his consecration.",
            
            "legacy": "He prepared Poland spiritually for everything that came after. His courage showed people that faith was stronger than fear. When Karol Wojtyła became Pope John Paul II, it was Wyszyński's years of faithful witness that made Poland ready. The Primate held the ground, kept the faith alive, so that when freedom came, Poland's Catholic soul was still intact."
        }
        
        return responses.get(aspect, responses["general"])

    @function_tool
    async def tell_about_prl_era(self, topic: str = "general"):
        """Explain the communist era in Poland and the Church's role"""
        logger.info(f"🕊️ Visitor asking about PRL era: {topic}")
        
        responses = {
            "general": "The PRL - the Polish People's Republic - was a time of great suffering but also great faith, from 1952 to 1989. The communist regime, controlled by the Soviet Union, tried to erase God from Polish life. They closed churches, persecuted priests, forbade religious education. But the Polish people held fast to their faith. The Church became the one place they could not fully control, and so the Church became the heart of Polish resistance.",
            
            "persecution": "The persecution was severe. Priests were imprisoned, tortured, killed. Religious education was banned in schools. Parents who raised their children in the faith could lose their jobs. Children were pressured to reject their baptism. Saying the Rosary at home could bring trouble. It was a time when simply being faithful required courage. Every Sunday Mass was an act of resistance.",
            
            "church_resistance": "The Church never submitted. Cardinal Wyszyński was imprisoned. Other bishops were harassed. But they kept teaching, kept celebrating Mass, kept baptizing babies. Churches were always full - sometimes so crowded people stood outside. The regime could not break this. They had the guns and the police, but the Church had the truth and the people's hearts.",
            
            "solidarity": "In 1980, workers in Gdańsk went on strike. They hung a cross in the shipyard. They had chaplains. They prayed together. This was Solidarity - born from the courage the Church had nurtured for decades. For a brief time, before martial law in 1981, Poland breathed freedom. And that breath could not be taken back.",
            
            "papal_visits": "When John Paul II visited Poland in 1979, millions came to see him. The regime could not stop it. For nine days, Poland was free. People sang, prayed, wept. They remembered who they were - children of God, not slaves of the state. His words awakened something that could not be put back to sleep. By 1989, communism was finished."
        }
        
        return responses.get(topic, responses["general"])

    @function_tool
    async def tell_about_museum(self, question: str = "general"):
        """Provide information about the museum itself"""
        logger.info(f"🏛️ Visitor asking about museum: {question}")
        
        responses = {
            "general": "This museum is a sacred space, dear visitor. It houses the personal belongings, documents, and memories of these two great men. When you walk these halls, you are walking in the presence of holiness. We have items they touched, wore, wrote with their own hands. But more than that, this is a place of prayer. Many come not just to learn, but to pray, to seek intercession, to feel close to these holy men.",
            
            "collections": "Our collections are precious. We have papal vestments worn by John Paul II, his personal prayer books with his handwritten notes. We have letters Cardinal Wyszyński wrote from prison. Photographs from their lives. Documents from the PRL era. Each item tells a story of faith, courage, and love. Take your time with each one - they have much to teach us.",
            
            "hours": "We are open daily to welcome pilgrims and visitors. The museum opens its doors so that the legacy of these men can continue to inspire. Whether you have an hour or a whole afternoon, you are welcome here. This is a house of memory and prayer.",
            
            "visiting": "As you visit, I encourage you to move slowly. Pause. Pray. Let the stories sink into your heart. Some visitors light a candle in our chapel. Some sit in silence. Some weep - and that is good too. These men suffered so much, loved so much. Their witness deserves our tears and our gratitude."
        }
        
        return responses.get(question, responses["general"])

    @function_tool
    async def offer_prayer(self, intention: str = "general"):
        """Offer a prayer or blessing for the visitor"""
        logger.info(f"🙏 Offering prayer for: {intention}")
        
        return "Let us pause for a moment... May God bless you on your journey. May the courage of John Paul and Wyszyński inspire your own faith. May Mary, Mother of Poland and Mother of us all, protect you and guide you. And may you always remember: be not afraid, for God is with you. Amen."

    @function_tool
    async def recommend_next_stop(self):
        """Suggest what visitor should see next in museum"""
        logger.info("🚶 Suggesting next stop in museum")
        
        return "If you haven't yet, I encourage you to visit the section with Cardinal Wyszyński's personal effects from his imprisonment. There's a small prayer book he kept with him - when you see his handwritten prayers, it's deeply moving. After that, the collection of photographs from John Paul's papal visits to Poland is extraordinary. You'll see the faces of the people - the joy, the hope, the tears. It's unforgettable."

    @function_tool  
    async def answer_question(self, question: str):
        """Handle general questions from visitors"""
        logger.info(f"❓ Visitor question: {question}")
        
        return "That's a wonderful question. Let me share what I know... If you'd like more detailed information about John Paul II, Cardinal Wyszyński, the PRL era, or the museum itself, I'm happy to explore any of these topics more deeply with you. What aspect interests you most?"


async def entrypoint(ctx: agents.JobContext):
    """Entry point for the museum guide agent"""
    logger.info("🕊️ Starting Museum Tour Guide Agent")
    logger.info(f"📍 Room: {ctx.room.name}")
    
    # Create agent session with warm, friendly voice
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="nova",  # Warm, gentle voice perfect for elderly visitors
            temperature=0.8,  # Slightly creative for natural conversation
        )
    )
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=MuseumGuideAgent(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    logger.info("✅ Museum guide agent started")
    
    # Warm opening greeting
    await session.generate_reply(
        instructions="""Greet the visitor warmly as a spiritual tour guide. Say something like:

'Welcome, dear visitor, to the Museum of John Paul II and Primate Wyszyński. May peace be with you. I'm your guide today, and it's my joy to help you discover the remarkable lives of these two giants of faith who stood courageously against darkness and showed Poland - and the world - the power of faith and love.

What would you most like to know about? The life of Saint John Paul II? The heroic witness of Cardinal Wyszyński? Or perhaps the difficult years of communist rule when the Church kept hope alive?'

Speak slowly, warmly, with gentle reverence."""
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))