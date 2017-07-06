# -*- coding:utf-8 -*-
# filename:zhihuSpider.py
"""
2017/7/3
"""
# requirements
import re, os
import requests, cookielib, html2text, platform
from bs4 import BeautifulSoup

#fuck-login
from LoginZH import isLogin
from LoginZH import Logging


# 登陆验证
requests = requests.Session()
requests.cookies = cookielib.LWPCookieJar('cookies')
try:
    requests.cookies.load(ignore_discard=True)
except:
    Logging.error(u"你还没有登录知乎哦 ...")
    Logging.info(u"执行 'python LoginZH.py' 即可以完成登录。")
    raise Exception("无权限(403)")

if isLogin() != True:
    Logging.error(u"你的身份信息已经失效，请重新生成身份信息( `python LoginZH.py` )。")
    raise Exception("无权限(403)")
# 2017/7/14 已更新

# 问题操作类 获取所有答案 answer+content
class Question:
    url = None
    soup = None

    def __init__(self, url, title=None):
        # 2017/7/14修改，可支持收藏夹中的专栏文章
        if not re.compile(r"(http|https)://\w+.zhihu.com/\w+/\d{8}").match(url):
            raise ValueError("\"" + url + "\"" + " : it isn't a question url.")
        else:
            self.url = url

        if title != None: self.title = title

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/57.0.2987.98 Safari/537.36",
            }
        r = requests.get(self.url,headers=headers, verify=False)
        self.soup = BeautifulSoup(r.content, "lxml")

    def get_title(self):
        if hasattr(self, "title"):
            return self.title
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            title = soup.find("h1", class_="QuestionHeader-title").string.replace("\n", "")
            self.title = title
            return title

    def get_detail(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        detail = soup.find("span", class_="RichText").get_text()
        return detail

    def get_answers_num(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        if soup.find("h4", class_="List-headerText") != None:
            answers_num = int(re.compile(r"\d+").match(soup.find_all("h4")[0].get_text()).group())
        else:
            answers_num = 'no answer yet..'
        return answers_num

    def get_followers_num(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        followers_num = int(soup.find("div", class_="NumberBoard-value").string)
        return followers_num

    def get_topics(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        topic_tag = soup.find_all("div", class_="Tag QuestionTopic")
        topics = []
        for topic_list in topic_tag:
            topic = topic_list.get_text()
            topics.append(topic)
        topics = '/'.join(topics)
        return topics

    #def get_all_answers(self):
        #待修复
        
    def get_visit_times(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        visit_times = int(soup.find_all("div", class_="NumberBoard-value")[1].string)
        return visit_times

# 答案操作类
class Answer:
    answer_url = None
    # session = None
    soup = None

    def __init__(self, answer_url, question=None, author=None, upvote=None, content=None):

        self.answer_url = answer_url
        if question != None:
            self.question = question
        if author != None:
            self.author = author
        if upvote != None:
            self.up_vote = upvote
        if content != None:
            self.content = content

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36", }
        r = requests.get(self.answer_url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_question(self):
        if hasattr(self, "question"):
            return self.question
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            question_link = soup.find("a", class_="QuestionMainAction")
            url = "http://www.zhihu.com" + question_link["href"]
            title = soup.find("h1", class_="QuestionHeader-title").string.replace("\n", "")
            question = Question(url, title)
            return question

    def get_author(self):
        if hasattr(self, "author"):
            return self.author
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            authors_info = soup.find_all("a", class_="UserLink-link")

            for author_tag in authors_info:
                author_id = author_tag.get_text()
                author_url = author_tag['href']

            if author_id == u"匿名用户":
                author_url = None
                author = User(author_url)
            else:
                author = User(author_url, author_id)
            return author

    def get_upvote(self):
        if hasattr(self, "up_vote"):
            return self.up_vote
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup

            # 具体到个位的是str，不便后期分析，但可以用re匹配出来。
            count = soup.find("button", class_="Button Button--plain").string
            count = soup.select("span[class=Voters]")[0].string
            pattern = re.compile(r'\d+')
            up_vote = int(pattern.match(count).group())

            return up_vote

    # for txt|md
    def get_content(self):
        if hasattr(self, "content"):
            return self.content
        else:
            if self.soup == None:
                self.parser()
            soup = BeautifulSoup(self.soup.encode("utf-8"), "lxml")
            answer = soup.find("div", class_="RichContent-inner")
            edit_time = soup.find("div", class_="ContentItem-time")
            soup.body.extract()
            soup.head.insert_after(soup.new_tag("body", **{'class': 'zhi'}))
            soup.body.append(answer)
            soup.body.append(edit_time)
            img_list = soup.find_all("img", class_="content_image lazy")
            for img in img_list:
                img["src"] = img["data-actualsrc"]
            img_list = soup.find_all("img", class_="origin_image zh-lightbox-thumb lazy")
            for img in img_list:
                img["src"] = img["data-actualsrc"]
            noscript_list = soup.find_all("noscript")
            for noscript in noscript_list:
                noscript.extract()
            content = soup
            self.content = content
            return content

    # from https://github.com/egrcc/zhihu-python
    def to_txt(self):
        content = self.get_content()
        body = content.find("body")
        br_list = body.find_all("br")
        for br in br_list:
            br.insert_after(content.new_string("\n"))
        li_list = body.find_all("li")
        for li in li_list:
            li.insert_before(content.new_string("\n"))

        anon_user_id = "匿名用户"
        if self.get_author().get_user_id() == anon_user_id:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "text"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "text")))

            file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt"
            print file_name

            file_name = file_name.replace("/", "'SLASH'")
            if os.path.exists(os.path.join(os.path.join(os.getcwd(), "text"), file_name)):
                f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "a")
                f.write("\n\n")
            else:
                f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "a")
                f.write(self.get_question().get_title() + "\n\n")
        else:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "text"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "text")))

            file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt".decode(
                'utf-8')
            print file_name

            file_name = file_name.replace("/", "'SLASH'")
            f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "wt")
            f.write(self.get_question().get_title().encode('utf8') + "\n\n")

        f.write("作者: " + self.get_author().get_user_id().encode('utf-8') + "  赞同: " + str(self.get_upvote()) + "\n\n")
        f.write(body.get_text().encode("utf-8"))
        f.write("\n" + "原链接: " + self.answer_url)
        f.close()

    def to_md(self):
        content = self.get_content()

        anon_user_id = "匿名用户"
        if self.get_author().get_user_id() == anon_user_id:
            file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md"
            print file_name

            file_name = file_name.replace("/", "'SLASH'")
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "markdown"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "markdown")))
            if os.path.exists(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name)):
                f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "a")
                f.write("\n")
            else:
                f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "a")
                f.write("# " + self.get_question().get_title() + "\n")
        else:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "markdown"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "markdown")))
            file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md".decode('utf-8')
            print file_name

            file_name = file_name.replace("/", "'SLASH'")
            f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "wt")
            f.write("# " + self.get_question().get_title().encode('utf-8') + "\n")
        f.write("### 作者: " + self.get_author().get_user_id().encode('utf-8') + "  赞同: " + str(self.get_upvote()) + "\n")
        text = html2text.html2text(content.decode('utf-8')).encode("utf-8")

        r = re.findall(r'\*\*(.*?)\*\*', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'_(.*)_', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'!\[\]\((?:.*?)\)', text)
        for i in r:
            text = text.replace(i, i + "\n\n")

        f.write(text)
        f.write("\n---\n#### 原链接: " + self.answer_url)
        f.close()


    # 2017/7/4  接口失效
    #def get_voters(self):
    
# 用户信息操作类
class User:
    user_url = None
    soup = None

    def __init__(self, user_url, user_id=None):
        if user_url == None:
            self.user_id = "匿名用户"
        # 避免企业号冲突，有特殊需要可以添加'www.zhihu.com/org'
        #elif user_url.startswith(r'www.zhihu.com/people', user_url.index('//') + 2) == False:
        #    raise ValueError("\"" + user_url + "\"" + " : it isn't a user url.")
        else:
            self.user_url = user_url
            if user_id != None:
                self.user_id = user_id

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
            }
        r = requests.get(self.user_url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_user_id(self):
        if self.user_url == None:
            return "匿名用户"
        else:
            if hasattr(self, "user_id"):
                return self.user_id
            else:
                if self.soup == None:
                    self.parser()
                soup = self.soup
                user_id = soup.find("span", class_="ProfileHeader-name").string
                self.user_id = user_id
                return user_id

    def get_head_img_url(self, scale=4):
        """
            获取知乎用户的头像url
        """
        if self.user_url == None:
            print "I'm anonymous user."
            return None
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            url = soup.find("img", class_="Avatar Avatar--large UserAvatar-inner")["src"]
            return url

    # 2017/7/4 已失效
    #def get_data_id(self):

    def get_gender(self):
        """
            获取性别
        """
        if self.user_url == None:
            print "I'm anonymous user."
            return 'unknown'
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            try:
                gender = str(soup.find("div", class_="ProfileHeader-iconWrapper").i)
                if (gender == '<svg class="icon icon-profile-female"></i>'):
                    return 'female'
                else:
                    return 'male'
            except:
                return 'unknown'

    def get_followees_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            followees_num = int(soup.find("div", class_="NumberBoard-value").string)
            return followees_num

    def get_followers_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            followers_num = int(soup.find_all("div", class_="NumberBoard-value")[1].string)
            return followers_num

    # 同样的方式可以获取该用户关注的Live、专栏、问题、收藏夹等
    def get_topics_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            topics_num = int(soup.find_all("a", class_="Profile-lightItem", href=re.compile('/topics'))[0].contents[1].string)
            return topics_num

    # 个人成就agree/thanks/collection抓取
    #def get_agree_num(self):
    #def get_thanks_num(self):
    #def get_collec_num(self):

    def get_asks_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            asks_num = int(soup.find_all("span", class_="Tabs-meta")[0].string)
            return asks_num

    def get_answers_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            answers_num = int(soup.find_all("span", class_="Tabs-meta")[1].string)
            return answers_num

    def get_collections_num(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            collections_num = int(soup.find_all("span", class_="Tabs-meta")[3].string)
            return collections_num

# 收藏夹操作类,修改colleciton避免同名库冲突
class Collection_zh:
    url = None
    soup = None

    def __init__(self, url, name=None, creator=None):
        # 删除了多余url判断。
        self.url = url
        # print 'collection url',url
        if name != None:
            self.name = name
        if creator != None:
            self.creator = creator

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
        }
        r = requests.get(self.url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_name(self):
        if hasattr(self, 'name'):
            if platform.system() == 'Windows':
                return self.name.decode('utf-8').encode('gbk')
            else:
                return self.name
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            self.name = soup.find("h2", id="zh-fav-head-title").string.encode("utf-8").strip()
            if platform.system() == 'Windows':
                return self.name.decode('utf-8').encode('gbk')
            return self.name

    def get_creator(self):
        if hasattr(self, 'creator'):
            return self.creator
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            creator_id = soup.find("h2", class_="zm-list-content-title").a.string.encode("utf-8")
            creator_url = "http://www.zhihu.com" + soup.find("h2", class_="zm-list-content-title").a["href"]
            creator = User(creator_url, creator_id)
            self.creator = creator
            return creator

    def get_all_answers(self):
        global answer_url
        if self.soup == None:
            self.parser()
        soup = self.soup
        answer_list = soup.find_all("div", class_="zm-item")
        if len(answer_list) == 0:
            print "the collection is empty."
        else:
            question_url = None
            question_title = None
            for answer in answer_list:
                question_link = answer.find("h2")

                if question_link != None:
                    if answer["data-type"] == "Answer":
                        question_url = "http://www.zhihu.com" + question_link.a["href"]
                        answer_url = "http://www.zhihu.com" + answer.find("div", class_="zh-summary summary clearfix").a[
                            "href"]
                    elif answer["data-type"] == "Post":
                        question_url = question_link.a["href"]
                        answer_url = answer.find("div", class_="zh-summary summary clearfix").a["href"]

                    question_title = question_link.a.string.encode("utf-8")
                question = Question(question_url, question_title)

                # try暂且跳过NoneType类型
                try:
                    if answer.find("a", class_="author-link").get_text(strip='\n') == "匿名用户":
                        author_url = None
                        author = User(author_url)
                    else:
                        author_tag = answer.find("a", class_="author-link")
                        author_id = author_tag.string.encode("utf-8")
                        author_url = "http://www.zhihu.com" + author_tag["href"]
                        author = User(author_url, author_id)
                    yield Answer(answer_url, question, author)
                except:
                    pass
            i = 2
            while True:
                headers = {
                    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
                }
                r = requests.get(self.url + "?page=" + str(i), headers=headers, verify=False)
                answer_soup = BeautifulSoup(r.content, "lxml")
                answer_list = answer_soup.find_all("div", class_="zm-item")
                if len(answer_list) == 0:
                    break
                else:
                    for answer in answer_list:
                        question_link = answer.find("h2")

                        if question_link != None:
                            if answer["data-type"] == "Answer":
                                question_url = "http://www.zhihu.com" + question_link.a["href"]
                                answer_url = "http://www.zhihu.com" + \
                                             answer.find("div", class_="zh-summary summary clearfix").a["href"]
                            elif answer["data-type"] == "Post":
                                question_url = question_link.a["href"]
                                answer_url = answer.find("div", class_="zh-summary summary clearfix").a["href"]

                            question_title = question_link.a.string.encode("utf-8")
                        question = Question(question_url, question_title)
                        author = None

                        if answer.find("a", class_="author-link").get_text(strip='\n') == u"匿名用户":
                            author_url = None
                            author = User(author_url)
                        else:
                            author_tag = answer.find("a", class_="author-link")
                            author_id = author_tag.get_text(strip='\n')
                            author_url = "http://www.zhihu.com" + author_tag["href"]
                            author = User(author_url, author_id)
                        yield Answer(answer_url, question, author)
                i += 1

    def get_top_i_answers(self, n):
        j = 0
        answers = self.get_all_answers()
        for answer in answers:
            j = j + 1
            if j > n:
                break
            yield answer

# 专栏文章操作类
class Post:
    url = None
    meta = None
    slug = None

    def __init__(self, url):

        if not re.compile(r"(http|https)://zhuanlan.zhihu.com/p/\d{8}").match(url):
            raise ValueError("\"" + url + "\"" + " : it isn't a question url.")
        else:
            self.url = url
            self.slug = re.compile(r"(http|https)://zhuanlan.zhihu.com/p/(\d{8})").match(url).group(2)

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
            }
        r = requests.get('https://zhuanlan.zhihu.com/api/posts/' + self.slug, headers=headers, verify=False)
        self.meta = r.json()

    def get_title(self):
        if hasattr(self, "title"):
            return self.title
        else:
            if self.meta == None:
                self.parser()
        meta = self.meta
        title = meta['title']
        self.title = title
        return title

    def get_content(self):
        if hasattr(self, "content"):
            return self.content
        else:
            if self.meta == None:
                self.parser()
        meta = self.meta
        content = meta['content']
        self.content = content
        return content

    def get_author(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        author_tag = meta['author']
        author = User(author_tag['profileUrl'], author_tag['slug'])
        return author

    def get_column(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        column_url = 'https://zhuanlan.zhihu.com/' + meta['column']['slug']
        return Column(column_url, meta['column']['slug'])

    def get_likes(self):
        if hasattr(self, "likesCount"):
            return self.likesCount
        else:
            if self.meta == None:
                self.parser()
        meta = self.meta
        likesCount = int(meta["likesCount"])
        self.likeCount = meta["likesCount"]
        return likesCount

    def get_topics(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        topic_list = []
        for topic in meta['topics']:
            topic_list.append(topic['name'])
        topics = '/'.join(topic_list)
        print topics

# 专栏操作类
class Column:
    url = None
    meta = None

    def __init__(self, url, slug=None):

        if not re.compile(r"(http|https)://zhuanlan.zhihu.com/([0-9a-zA-Z]+)").match(url):
            raise ValueError("\"" + url + "\"" + " : it isn't a question url.")
        else:
            self.url = url
            if slug == None:
                self.slug = re.compile(r"(http|https)://zhuanlan.zhihu.com/([0-9a-zA-Z]+)").match(url).group(2)
            else:
                self.slug = slug

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
            }
        r = requests.get('https://zhuanlan.zhihu.com/api/columns/' + self.slug, headers=headers, verify=False)
        self.meta = r.json()

    def get_title(self):
        if hasattr(self,"title"):
            return self.title
        else:
            if self.meta == None:
                self.parser()
            meta = self.meta
            title = meta['name']
            self.title = title
            return title

    def get_description(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        description = meta['description']
        return description

    def get_followers_num(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        followers_num = int(meta['followersCount'])
        return followers_num

    def get_posts_num(self):
        if self.meta == None:
            self.parser()
        meta = self.meta
        posts_num = int(meta['postsCount'])
        return posts_num

    def get_creator(self):
        if hasattr(self, "creator"):
            return self.creator
        else:
            if self.meta == None:
                self.parser()
            meta = self.meta
            creator_tag = meta['creator']
            creator = User(creator_tag['profileUrl'],creator_tag['slug'])
            return creator

    def get_all_posts(self):
        posts_num = self.get_posts_num()
        if posts_num == 0:
            print "No posts."
            return
            yield
        else:
            for i in xrange((posts_num - 1) / 20 + 1):
                parm = {'limit': 20, 'offset': 20*i}
                url = 'https://zhuanlan.zhihu.com/api/columns/' + self.slug + '/posts'
                headers = {
                    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
                    }
                r = requests.get(url, params=parm, headers=headers, verify=False)
                posts_list = r.json()
                for p in posts_list:
                    post_url = 'https://zhuanlan.zhihu.com/p/' + str(p['slug'])
                    yield Post(post_url)


