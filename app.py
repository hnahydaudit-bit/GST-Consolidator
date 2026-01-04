AttributeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/gst-consolidator/app.py", line 84, in <module>
    tx, ig, cg, sg, cs = sum_summary_section(data.get(key,[]))
File "/mount/src/gst-consolidator/app.py", line 55, in sum_summary_section
    tx += e.get("txval",0)
















