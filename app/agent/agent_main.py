"""
Entry point pentru Agent CLI.

Usage:
    python agent_main.py "Mesajul tău"
    
Sau pentru mod interactiv:
    python agent_main.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from app.agent.agent import Agent


def interactive_mode():
    """Mod interactiv pentru chat cu agentul."""
    print("=" * 70)
    print("🤖 CivicAID Agent - Mod Interactiv")
    print("=" * 70)
    print("Scrie 'exit' sau 'quit' pentru a ieși")
    print("Scrie 'clear' pentru a șterge istoricul conversației")
    print("=" * 70)
    print()
    
    agent = Agent()
    
    while True:
        try:
            user_input = input("\n👤 Tu: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 La revedere!")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("✅ Istoricul conversației a fost șters.")
                continue
            
            print("\n🤖 Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 La revedere!")
            break
        except Exception as e:
            print(f"\n❌ Eroare: {e}")


def single_message_mode(message: str):
    """Mod pentru un singur mesaj."""
    agent = Agent()
    response = agent.chat(message)
    print(response)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Mod interactiv
        interactive_mode()
    else:
        # Mod CLI cu mesaj
        user_message = " ".join(sys.argv[1:])
        single_message_mode(user_message)

