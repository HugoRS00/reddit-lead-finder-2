import os
from typing import List, Dict, Optional
import re

class AIService:
    def __init__(self):
        """Initialize Anthropic client lazily."""
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            if api_key:
                self.client = Anthropic(api_key=api_key)
                print("Anthropic client initialized successfully")
            else:
                print("Warning: ANTHROPIC_API_KEY not set")
        except ImportError:
            print("Anthropic package not installed")
        except Exception as e:
            print(f"Failed to initialize Anthropic client: {e}")

    def generate_reply(self, context: str, intent_label: str, reply_mode: str, 
                      reply_length: str, voice_profile: Dict = None) -> Dict:
        """Generate AI reply with fallbacks."""
        if not self.client:
            return self._generate_template_fallback(context, intent_label, reply_mode, reply_length, voice_profile)

        voice_name = (voice_profile.get('name') or '').strip() if voice_profile else ''
        voice_instructions_raw = (voice_profile.get('instructions') or '').strip() if voice_profile else ''
        voice_instructions = voice_instructions_raw.replace('-', ' ').replace('–', ' ').replace('—', ' ')

        # Generate length-specific instructions
        length_instructions = {
            'short': "Keep it ultra short. One sentence with around ten words.",
            'medium': "Keep it to roughly five sentences. Provide detailed advice with line breaks between sentences.",
            'long': "Write at least seven sentences. Use line breaks between sentences and share thorough guidance."
        }
        length_line = length_instructions.get(reply_length, length_instructions['medium'])

        # Determine platform label (simple heuristic or passed in)
        platform_label = 'Social Media' 
        
        safe_intent = (intent_label or 'General discussion').replace('-', ' ')

        # Default voice if none provided
        if not voice_instructions:
            voice_instructions = (
                "strictly lowercase. minimal punctuation. no emojis. no 'ai' fluff. "
                "1-3 short sentences. max 50 words. "
                "structure: 1. the read (trend + signal). 2. the play (bias / entry / invalidation). "
                "anchors: always use specific numbers/levels. "
                "banned: greetings, disclaimers, 'key read:', 'i think', 'hope', 'buzzing', 'rocket'."
            )

        core_guidelines = [
            "Answer the question directly and reference details from the post.",
            "Share insight from real trading experience rather than generic tips.",
            "Use varied sentence lengths and keep the tone casual.",
            "Do not use hyphen characters or long dashes; choose commas or new sentences instead."
        ]

        if voice_instructions:
            core_guidelines.insert(1, f"Match this tone: {voice_instructions}")
        elif voice_name:
            core_guidelines.insert(1, f"Match the tone described as {voice_name}.")

        mode_guidelines = {
            'ghost': [
                "Keep brand mentions out of the reply.",
                "Focus entirely on helping the poster."
            ],
            'soft': [
                "Mention TradingWizard AI once as a helpful option without adding a link.",
                "Keep the mention light and friendly."
            ],
            'full': [
                "Mention TradingWizard.ai once with https://tradingwizard.ai and make it feel natural.",
                "Add a casual disclosure such as (I help build it)."
            ]
        }

        directives = core_guidelines + mode_guidelines.get(reply_mode, mode_guidelines['full'])
        directives.append(length_line)
        directives_text = "\n".join(f"{idx}. {line}" for idx, line in enumerate(directives, start=1))

        prompt = (
            f"You are a battle tested trader replying on {platform_label}. Sound like a real human friend.\n\n"
            f"Here is the post:\n<<<\n{context}\n>>>\n\n"
            f"Topic: {safe_intent}\n\n"
            f"Guidelines:\n{directives_text}\n\n"
            f"Write the reply now."
        )

        try:
            variants = []
            for i in range(3):
                variant_prompt = prompt + f"\n\nGenerate variant {chr(65+i)}. Make it slightly different in tone and style while keeping the same core message."
                
                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514", # Assuming this model exists or fallback to 3.5
                    max_tokens=400,
                    messages=[{
                        "role": "user",
                        "content": variant_prompt
                    }]
                )
                
                variant_reply = message.content[0].text
                processed_reply = self._add_line_breaks_if_needed(variant_reply)
                variants.append({
                    'letter': chr(65+i),
                    'reply': processed_reply
                })
            
            return {
                'success': True,
                'variants': variants,
                'method': 'ai'
            }
            
        except Exception as e:
            print(f"AI generation failed: {e}")
            return self._generate_template_fallback(context, intent_label, reply_mode, reply_length, voice_profile, error=str(e))

    def _add_line_breaks_if_needed(self, text: str) -> str:
        """Add line breaks between sentences if there are 4 or more sentences."""
        # Split by sentence endings (. ! ?) but keep the punctuation
        sentences = re.split(r'([.!?])\s+', text)
        
        # Reconstruct sentences with punctuation
        reconstructed_sentences = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                reconstructed_sentences.append(sentence.strip())
            elif sentences[i].strip():
                reconstructed_sentences.append(sentences[i].strip())
        
        # Filter out empty sentences
        sentences = [s for s in reconstructed_sentences if s.strip()]
        
        if len(sentences) >= 4:
            return '\n\n'.join(sentences)
        return text

    def _generate_template_fallback(self, context, intent_label, reply_mode, reply_length, voice_profile, error=None):
        """Generate template-based replies."""
        voice_instructions = (voice_profile.get('instructions') or '') if voice_profile else ''
        
        variants = []
        for i in range(3):
            variant_reply = self._generate_single_template(
                context, intent_label, reply_mode, reply_length, i, voice_instructions
            )
            processed_reply = self._add_line_breaks_if_needed(variant_reply)
            variants.append({
                'letter': chr(65+i),
                'reply': processed_reply
            })
            
        return {
            'success': True,
            'variants': variants,
            'method': 'template_fallback',
            'error': error,
            'warning': 'AI generation unavailable'
        }

    def _generate_single_template(self, context, intent_label, reply_mode, reply_length, variant, voice_instructions):
        tips = {
            'Tool-seeking': "Start by defining your timeframe and setup type. Map key support and resistance levels, then confirm with momentum indicators. Focus on keeping your edge simple and repeatable.",
            'How-to': "Break it into steps: define what you're analyzing, overlay key levels, add one or two confirmation indicators, and document your rules. Simple beats complex every time.",
            'Problem-solving': "Common issue: too many conflicting indicators. Strip it down to price action, volume, and one momentum indicator. Also check if you're trading during choppy hours.",
            'General discussion': "For consistent results, document your setups, track your stats, and refine what actually performs instead of what just feels good."
        }
        
        tip = tips.get(intent_label, tips['General discussion'])
        
        if reply_length == 'short':
            ultra_short_tips = {
                'Tool-seeking': "Price action + volume.",
                'How-to': "Price, levels, momentum.",
                'Problem-solving': "Price action only.",
                'General discussion': "Track everything."
            }
            tip = ultra_short_tips.get(intent_label, "Keep it simple.")
        elif reply_length == 'long':
            tip += "\n\nRemember to backtest your strategy and keep detailed logs of your trades for continuous improvement."
        
        if variant == 1:
            tip = tip.replace("Start by", "First, I'd").replace("Break it", "Honestly, break it").replace("Common issue", "Yeah, common issue")
        elif variant == 2:
            tip = tip.replace("Start by", "IMO, start by").replace("Break it", "Tbh, break it").replace("Common issue", "Fwiw, common issue")

        clean_voice = (voice_instructions or '').replace('-', ' ').replace('–', ' ').replace('—', ' ').strip()
        voice_hint = clean_voice.lower()
        opener = ""
        if voice_hint:
            if any(word in voice_hint for word in ['casual', 'buddy', 'friend', 'slang']):
                opener = "Yo, appreciate you bringing this up. "
            elif any(word in voice_hint for word in ['mentor', 'supportive', 'coach']):
                opener = "Happy you asked this, let's walk through it. "
            elif any(word in voice_hint for word in ['direct', 'no fluff', 'straight']):
                opener = "Straight talk ahead. "
            
            if opener and reply_length == 'short':
                opener = opener.strip() + " "

        if reply_length == 'short':
            if reply_mode == 'ghost':
                cta = " Use tools."
            elif reply_mode == 'soft':
                cta = " TradingWizard AI helps."
            else:
                cta = " TradingWizard.ai for analysis. (I help build it)"
        else:
            if reply_mode == 'ghost':
                cta = " Tools that automate chart reading and setup identification can speed this up significantly."
            elif reply_mode == 'soft':
                cta = " TradingWizard AI can help automate chart analysis and pattern recognition for any symbol you're interested in."
            else:
                cta = " If you want AI powered analysis for any chart, TradingWizard.ai gives an instant technical breakdown when you pick the symbol. (Disclosure: I help build it)"
        
        if opener:
            return opener + tip + cta
        return tip + cta
