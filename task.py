from ingest import ingest_docs, ingest_text
from evaluate_agent import evaluate_agent
import crud


# background task of generating the report
async def generate_report(
    interview_id,
    result,
    db_session,
):
    resume_vs = await ingest_docs(
        index="r_" + result["resume"].id, input=result["resume"].resource
    )
    job_vs = await ingest_text(
        index="j_" + result["job"].id, input=result["job"].content
    )
    chat_history = await ingest_text(
        index="h_" + result["interview"].id, input=str(result["interview"].history)
    )

    evaluate = evaluate_agent(resume_vs, job_vs, chat_history)
    job_title = result["job"].title if result["job"].title is not None else "this job"
    job_prompt = f"Please suggest a highly personalized and custom checklist of action items to helping me get {job_title}. The action items should be as specific to this job as possible. Please provide minimal 5-10 items and order the item with the impact from high to low. Please reply the checklist in markdown format."

    evaluate_result = await evaluate.arun(input=job_prompt)

    result = {"evaluation": evaluate_result}
    #  update the result
    crud.add_interview_result(db_session, interview_id, "evaluation", evaluate_result)


async def generate_mock(
    interview_id,
    result,
    db_session,
):
    resume_vs = await ingest_docs(
        index="r_" + result["resume"].id, input=result["resume"].resource
    )
    job_vs = await ingest_text(
        index="j_" + result["job"].id, input=result["job"].content
    )
    chat_history = await ingest_text(
        index="h_" + result["interview"].id, input=str(result["interview"].history)
    )

    evaluate = evaluate_agent(resume_vs, job_vs, chat_history)
    job_title = result["job"].title if result["job"].title is not None else "this job"
    evaluate_result = await evaluate.arun(
        input=f"Please come up with one mock interview question for {job_title}. Then provide a high quality answer based on my resume and interview history. Your suggested answer should include specific information from my resume. In response, provide the mock question with 'Q:' and the suggested answer in 'A:"
    )
    crud.add_interview_result(db_session, interview_id, "mock", evaluate_result)
