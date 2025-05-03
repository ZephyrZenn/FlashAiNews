import datetime

SUMMARY_LENGTH = 500
DEFAULT_FEED_LAST_USED_DATE = datetime.datetime(1970, 1, 1, 0, 0, 0)

DEFAULT_PROMPT = """
```xml
<instruction>
You are tasked with synthesizing multiple news articles into a single, concise summary. Follow these steps to complete the task:

1. **Read the Input Articles**: You will receive a set of articles in JSON format. Each article contains a title and content. The content may include HTML tags, which you should ignore in your summary.

2. **Identify Core Themes**: As you read through the articles, look for common themes, major updates, and significant points of consensus or disagreement across the articles. 

3. **Synthesize Information**: Combine the insights from all articles into one integrated summary. Focus on the bigger picture rather than detailing individual articles. 

4. **Maintain Brevity**: Your summary should be concise, ideally between 800-1000 words. Use clear and direct language to ensure it is easily digestible for a quick read.

5. **Output Format**: Present your summary in JSON format with two attributes: "title" and "content". The "title" should be a brief descriptor of the summary, while the "content" should contain the synthesized overview using clean Markdown formatting.

6. **Avoid XML Tags**: Ensure that your output does not contain any XML tags, only the specified JSON format.

</instruction>

<examples>
<example>
<Input>
{
  "articles": [
    {
      "title": "Economic Growth in Q3",
      "content": "<p>The economy grew by 3% in the third quarter...</p>"
    },
    {
      "title": "Job Market Trends",
      "content": "<p>Unemployment rates have dropped to 4%...</p>"
    }
  ]
}
</Input>
<Output>
{
  "title": "Economic and Job Market Overview",
  "content": "The latest reports indicate a robust economic growth of 3% in Q3, coupled with a decline in unemployment rates to 4%. This suggests a strengthening job market, with positive implications for consumer spending and overall economic stability."
}
</Output>
</example>

<example>
<Input>
{
  "articles": [
    {
      "title": "Climate Change Initiatives",
      "content": "<p>New policies aim to reduce carbon emissions...</p>"
    },
    {
      "title": "Renewable Energy Growth",
      "content": "<p>Investment in solar and wind energy is surging...</p>"
    }
  ]
}
</Input>
<Output>
{
  "title": "Climate Change and Renewable Energy",
  "content": "Recent initiatives focused on combating climate change emphasize significant reductions in carbon emissions. Concurrently, investments in renewable energy sources, particularly solar and wind, are experiencing unprecedented growth, indicating a shift towards sustainable energy solutions."
}
</Output>
</example>

<example>
<Input>
{
  "articles": [
    {
      "title": "Tech Industry Innovations",
      "content": "<p>AI technology is transforming various sectors...</p>"
    },
    {
      "title": "Cybersecurity Challenges",
      "content": "<p>Increased cyber threats are prompting new security measures...</p>"
    }
  ]
}
</Input>
<Output>
{
  "title": "Tech Innovations and Cybersecurity",
  "content": "The tech industry is witnessing transformative innovations driven by AI, impacting multiple sectors. However, this rapid advancement is accompanied by rising cybersecurity challenges, necessitating the implementation of enhanced security measures to protect sensitive data."
}
</Output>
</example>
</examples>
```
"""
