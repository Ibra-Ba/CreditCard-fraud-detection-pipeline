import requests
from src.config import SLACK_WEBHOOK_URL


def send_alert(record: dict) -> None:
    """
    Envoie une alerte Slack quand une fraude est détectée.
    Ne lève pas d'exception si le webhook échoue —
    le consumer ne doit pas s'arrêter pour une alerte ratée.
    """
    if not SLACK_WEBHOOK_URL:
        print("[ALERT] SLACK_WEBHOOK_URL non configuré — alerte ignorée.")
        return

    message = (
        f":rotating_light: *Fraude détectée*\n"
        f"• Transaction : `{record['trans_num']}`\n"
        f"• Montant     : *{record['amt']} €*\n"
        f"• Catégorie   : {record['category']}\n"
        f"• Score       : {record['fraud_score']}\n"
        f"• Carte       : {record.get('cc_num', 'N/A')}"
    )

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5,
        )
        response.raise_for_status()
        print(f"[ALERT] Slack notifié — {record['trans_num']}")
    except Exception as e:
        print(f"[ALERT] Échec envoi Slack : {e}")