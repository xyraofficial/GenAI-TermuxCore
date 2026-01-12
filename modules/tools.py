import datetime
from googlesearch import search as gsearch

def get_realtime_info():
    now = datetime.datetime.now()
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    time_str = now.strftime('%d %B %Y - %H.%M') 
    return f"Waktu Sistem: {days[now.weekday()]}, {time_str}"

def google_search_tool(query):
    try:
        results = []
        for res in gsearch(query, num_results=3, advanced=True):
            results.append(f"TITLE: {res.title}\nDESC: {res.description}\nLINK: {res.url}")
        return "HASIL PENCARIAN:\n\n" + "\n\n".join(results) if results else "Tidak ada hasil."
    except Exception as e:
        return f"Error Search: {e}"
