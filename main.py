import asyncio
from utils.monitoring import setup_monitoring
from agents import cv_writer
from agents import project_analyser
from agents import job_analyser
from utils.userinput import read_user_input
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(dotenv_path=os.getenv("SECRETS_PATH"))
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set")
    exit(1)
#tools
#1. get project summaries
#2. get user input info
#3. create cv


async def main():
    setup_monitoring()

    
    step = True
    while step:
        print("Agent is staring, please wait...")
        user_input = read_user_input()

        print("Analyzing your projects...")
        project_summaries = await project_analyser.get_project_summaries()


        cv_created = False
        while not cv_created:
            print("Analysing jobs...")
            jobs = await job_analyser.job_analyser(project_summaries, user_input)

            #Only the jobs with relevance > 5
            jobs = jobs[jobs['relevance'] > 5]
            for _, j in jobs.iterrows():
                print("\nI have found a job that might interest you:")
                print(f"{j['company']} - {j['title']}:\nJob URL: {j['job_url']}\nSummary: {j['summary']}\n")
                chioce = input('Do you want to apply and write CV for this job? (y/n) ')
                if chioce.lower() in ['y','yes']:
                    cv_created = True
                    #make cv
                    print("Your cv is being written...")
                    cv_text = await cv_writer.write_cv(job=j, user_info=user_input, project_summaries=project_summaries)
                    print("\nYour CV is ready!\n")
                    print(cv_text)
                    save = input("Do you want to save this cv? (y/n) ")
                    if save.lower() in ['y','yes']:
                        with open(f"CVs/{j['company']}_{j['title']}_cv.txt", "w", encoding="utf-8") as f:
                            f.write(cv_text)
                    print("I will now check your cv for general impression, critical issues, and corrections\n")
                    check_result= await cv_writer.check_cv(cv_text)
                    print(f"\nGeneral impression:\n{check_result.general_impression}")
                    print(f"Critical issues:\n{check_result.critical_issues}")
                    print(f"Suggested corrections:\n {check_result.corrections}")
        
        step = input("Do you want to continue? (if yes, you can provide another input, before you hit enter)(y/n): ")
        if step.lower() not in ['y','yes']:
            step = False    
        
            
            

if __name__ == "__main__":
    asyncio.run(main())
    