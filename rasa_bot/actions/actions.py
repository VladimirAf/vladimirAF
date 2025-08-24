import os
import requests
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

RAG_URL = os.getenv("RAG_URL", "http://rag:8000")


class ActionRagQuery(Action):
    def name(self) -> Text:
        return "action_rag_query"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_msg = (tracker.latest_message or {}).get("text", "")
        try:
            resp = requests.post(f"{RAG_URL}/query", json={"query": user_msg, "top_k_retriever": 5, "top_k_reader": 3}, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer") or "Не нашла точного ответа."
            sources = data.get("sources", [])
            if sources:
                first = sources[0]
                source_str = first.get("source")
                dispatcher.utter_message(text=f"{answer}\n\nИсточник: {source_str}")
            else:
                dispatcher.utter_message(text=answer)
        except Exception as e:
            dispatcher.utter_message(text=f"Ошибка при обращении к базе знаний: {e}")
        return []