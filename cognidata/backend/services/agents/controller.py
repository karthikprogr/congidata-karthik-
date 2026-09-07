'''
Controller - pure rule-based routing. Zero LLM calls.
'''
def decide(question: str) -> str:
    q = question.lower()
    # Report agent
    if any(k in q for k in ['generate report','pdf report','create report','export report','download report']): return 'report'
    # Geo agent
    if any(k in q for k in ['map','city','region','geo','location','country','latitude','longitude','cities']): return 'geo'
    # SQL agent
    if any(k in q for k in ['sql','select','where','group by','count','show top','show me','list all','find all']): return 'sql'
    # RAG agent
    if any(k in q for k in ['document','context','what is','according to','based on','from the','rag','knowledge']): return 'rag'
    # Visualization
    if any(k in q for k in ['plot','chart','graph','visuali','dashboard','histogram','scatter','bar chart','pie chart']): return 'visualization'
    # ML
    if any(k in q for k in ['forecast','predict','future','model','regression','classify','cluster','train']): return 'ml'
    # Insight (prioritize simple comparison questions)
    if any(k in q for k in ['which','who','what','sells more','doing better','highest','lowest','best','worst','top','bottom','insight','summary','explain','why','trend','pattern','analyze','analysis']): return 'insight'
    # Anomaly
    if any(k in q for k in ['anomaly','outlier','unusual','abnormal','spike','detect']): return 'anomaly'
    return 'data'
