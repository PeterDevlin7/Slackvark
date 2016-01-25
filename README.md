The Problem: Every day, companies and their employees run into problems that they have trouble solving. Undoubtedly, the people with the expertise to help with these problems are out there. But an efficient market that connects the two in real-time doesn’t exist.

The Solution: A bot that companies can add to Slack that connects employees that have questions/problems with experts that have the answers, in real time, via instant message.

The experience, at a high level:
An employee poses a question or problem to Slackvark (the bot in Slack).
Slackvark sifts through its expert network to find the right person to address the question/problem.
Once there’s a match, the expert is sent a web link that allows them to chat directly with the questioner. The questioner just continues interacting right within Slack. This is a Slack(questioner)-to-Web(answerer) seamless chatting experience (talkus.io is a great example of how the Slack-to-web connection works).

The expert network: This is a highly curated network of quality startup folks that we will build over time. It includes experts on product, engineering, infrastructure, marketing, sales, funding, ops, customer service, accounting, and legal.

Why this is compelling now: Aardvark, a Gchat bot that connected questioners and answerers in real-time via instant message, was bought by Google for $50M back in 2010 because it was perceived to be a threat to algorithmic search. Google ended up shutting Aardvark down. Aardvark’s two major problems were the platform it was built for (poor 3rd party developer support) and the quality of its network (zero curation, anyone could join). Enter the emergence of Slack as a major platform for enterprise innovation along with its top-notch native support for bots/integrations, and the ingredients for a multi-billion dollar market have come together in 2016.

One alternative we’re considering: Legal questions have stood out as the most consistent pain point for tech startups and their employees. One thing we’re considering is launching with a niche product that focuses exclusively on legal questions (with the idea of spreading to the other topics over time, in a more controlled manner). A LegalSlackvark, if you will. We’re still in the process of deciding between a vertical go-to-market approach (legal only) or a horizontal go-to-market approach (all categories straight away). TBD!

Here’s what needs to get built for Slackvark v1 (all of this is subject to change as we work on it and learn more):

Company website
To allow experts to apply and companies to get added to our waitlist.
Great example: http://infos.getbirdly.com/
Part of the company website: allows experts to apply to become part of Slackvark’s expert network.
This will be part of the website that allows people to apply to become a Slackvark expert.
The incentive is that this allows you to build up your profile within the startup community and get connected to top startups with interesting problems. It could also lead to consulting and advising gigs. In general, it’s for experts that like to help startups.
There would be some ‘How it works’ content on this landing page.
The application process would ask for the following:
Area(s) of expertise (Product, Legal, UI/UX, Marketing, Funding, Accounting, Ops, Sales, Programming, Infrastructure)
Profiles (LinkedIn, Github, Quora, Stackoverflow, Twitter, Angel.co)
How often they’d be available to have 5 minute chats with questioners
Three other experts that they’d recommend and an incentive for each one that we’d approve.
We’d manually approve each applicant.
Once approved, a confirmation email would get sent to them.
Part of the company website: allows companies to apply for access to add Slackvark to their company’s Slack.
This will be a landing page that allows companies to apply.
The application process would ask for the following:
Tell us about your company and what you do
What stage is your company at?
How many of your employees are on Slack?
List three recent questions/problems that your company could have used help for
We will manually whitelist companies
When whitelisted, a confirmation email with install instructions will go out
Once installed, a Slackvark bot and a Slackvark channel will be added to the Company’s Slack and Slackvark will send an introductory how it works message.
The Slackvark bot:
Employees can pose questions/problems in three ways: 1- directly message the Slackvark bot 2- ask the question in the Slackvark channel that we automatically added to the company’s Slack when they signed up and 3 - with a / command
Slackvark detects whether a message is a question/problem. If yes, it confirms that that’s the question you’d like to ask. If not, it asks you how it can help.
First ask for the category of question like instawell?
Then Slackvark asks which category(s) your question fits into by listing them out with numbers that the user can choose from.
Then Slackvark asks you if you’d like to stay anonymous.
Once confirmed, Slackvark informs the questioner that it is looking for experts and that it will let them know when it finds one. It then notifies relevant experts (relevant = experts listed in the db under the category(s) that the questioner chose when asking the question).
How Slackvark notifies experts still needs to be decided (txt message, email, push notifications, how often, email digest, ask if we should dial it down, etc.).
If no experts accept:
If nobody accepts within 2 minutes, Slackvark reassures the questioner that it is still looking. Then again at the 5 minute mark.
At the 10 minute mark, Slackvark circles back and tells the questioner that it will report back if it ends up finding someone to answer.
If an expert accepts:
If the questioner doesn’t accept within 2 minutes, the expert gets notified that Slackvark is still waiting and the questioner gets pinged again by Slackvark. At the 5 minute mark, the question is shut down and both sides are notified.
Once an expert accepts, Slackvark reveals their identity to the questioner and asks if they’d like to accept and whether they’d like to reveal their identity or stay anonymous. The expert is notified that Slackvark is waiting for the questioner to accept.
This can happen with multiple expert acceptances.
Once the questioner accepts, Slackvark links to a new channel within Slack for the questioner and sends a weblink for the answerer. The two sides can synchronously chat with each other now (see Trustus.io’s demo for a good example of this Slack-to-web chat experience). Slackvark introduces the two sides to each other and sets a 5 minute time limit.
Can either side end the conversation prematurely? If yes, what is the experience?
Once 5 minutes are up, the Slackvark notifies both sides and asks both sides if they’d like to continue for another 5 minutes. Each side has 2 minutes to accept.
At the end of the interaction: 
Both sides are asked to rate their experience.
We need to think through how to use machine learning to improve the system here.

Open questions:
What happens to the question/answer chat content after a conversation is over?
Can we utilize that content for SEO?
Do questioners and answerers get access to archives of this content? Where?
Is it searchable by other users?
How can the Slackvark bot encourage engagement?
More to come

Project areas:
Website/landing page
The application process for experts
The application process for companies
Standard homepage navigation/content
Responsive
Slackvark bot
Slack integration
Logic
Machine learning
Webchat interface for experts
Seamless/synchronous chat with Slack users
Responsive
Web login for experts
Settings/profile
Responsive
Web login for companies
Settings/profile
Responsive
Analytics
Website/landing page 
Slackvark bot
Webchat interface for experts
Web login for experts
Web login for companies

