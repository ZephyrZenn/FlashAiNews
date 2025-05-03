from app.services.feed_service import create_group, generate_brief
from services import retrieve_new_feeds

if __name__ == '__main__':
    # retrieve_new_feeds()
    generate_brief(1)
    # create_group("Test Group", "This is a test group", [1])
# urls =  parse_and_get_url('feed.opml')
# url = random.choice(list(urls.values()))
# print("Query:", url[0])
# print(get_content(url=url[0]))
