import json
from llm_helper import llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

def process_posts(raw_file_path, processed_file_path=None, logging=False):
    '''
    Process LinkedIn posts to extract metadata and unify tags.
    Arguments:
        raw_file_path -- Path to the raw JSON file containing LinkedIn posts.
        processed_file_path -- Path to save the processed JSON file with metadata and unified tags.
    '''

    enriched_posts = []

    with open(raw_file_path, encoding='utf-8') as file:
        posts = json.load(file)
        
        for post in posts:

            metadata = extract_metadata(post['text'])
            post_with_metadata = post | metadata

            if logging: print(f"post with metadata: {post_with_metadata}")

            enriched_posts.append(post_with_metadata)

    unified_tags = get_unified_tags(enriched_posts, logging=logging)
    
    for post in enriched_posts:
        current_tags = post['tags']
        new_tags = {unified_tags[tag] for tag in current_tags}
        post['tags'] = list(new_tags)

    with open(processed_file_path, encoding='utf-8', mode="w") as outfile:
        json.dump(enriched_posts, outfile, indent=4)


def extract_metadata(post):
    '''
    Extract metadata from a LinkedIn post using LLM.
    Arguments:
        post -- The LinkedIn post text.
    Returns:
        A dictionary containing line_count, language, and tags.
    '''
    
    knowledge_base = '''
    You are given a LinkedIn post. You need to extract number of lines, language of the post and tags.
    1. Return a valid JSON. No preamble. 
    2. JSON object should have exactly three keys: line_count, language and tags. 
    3. tags is an array of text tags. Extract maximum two tags.
    4. Language should be English or Hinglish (Hinglish means hindi + english)
    
    Here is the actual post on which you need to perform this task:  
    {post}
    '''

    prompt_template = PromptTemplate.from_template(knowledge_base)

    # Create the chain and invoke it
    chain = prompt_template | llm
    response = chain.invoke(
        input={
            "post": post
        }
    )

    try:
        json_parser = JsonOutputParser()
        response_json = json_parser.parse(response.content)
    except OutputParserException as e:
        print(f"Error parsing unified tags: {e}")
        raise OutputParserException("Unable to parse jobs due to the context length.")
    return response_json

def get_unified_tags(posts_with_metadata, logging=False):
    '''
    Docstring for get_unified_tags
    
    Arguments:
        posts_with_metadata -- List of posts with extracted metadata including tags.
        logging -- Boolean flag to enable logging.
    Returns:
        A dictionary mapping original tags to unified tags.
    '''
    unique_tags = set()
    
    for post in posts_with_metadata:
        unique_tags.update(post['tags'])

    unique_tags_list = ','.join(unique_tags)

    template = '''I will give you a list of tags. You need to unify tags with the following requirements,
    1. Tags are unified and merged to create a shorter list. 
       Example 1: "Jobseekers", "Job Hunting" can be all merged into a single tag "Job Search". 
       Example 2: "Motivation", "Inspiration", "Drive" can be mapped to "Motivation"
       Example 3: "Personal Growth", "Personal Development", "Self Improvement" can be mapped to "Self Improvement"
       Example 4: "Scam Alert", "Job Scam" etc. can be mapped to "Scams"
    2. Each tag should be follow title case convention. example: "Motivation", "Job Search"
    3. Output should be a JSON object, No preamble
    3. Output should have mapping of original tag and the unified tag. 
       For example: {{"Jobseekers": "Job Search",  "Job Hunting": "Job Search", "Motivation": "Motivation}}
    
    Here is the list of tags: 
    {tags}
    '''
    prompt_template = PromptTemplate.from_template(template)
    chain = prompt_template | llm
    response = chain.invoke(
        input={
                "tags": str(unique_tags_list)
            }
        )
    
    try:
        json_parser = JsonOutputParser()
        json_response = json_parser.parse(response.content)
    except OutputParserException as e:
        print(f"Error parsing unified tags: {e}")
        raise OutputParserException("Unable to parse jobs due to the context length.")
    return json_response


if __name__ == "__main__":
    process_posts(
        raw_file_path="data/raw_posts.json",
        processed_file_path="data/processed_posts.json",
        logging=True
    )