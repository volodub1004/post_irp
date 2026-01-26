# Logbook
## 30/05/2025 First meeting with AIP
Me, Ken, Antony and Yassine

Discussed:
- Project Background: commerical gearing, maintaining, updating and validating client contacts.
- Collaboration: Still independent but work in the grand scheme may be in part colloborative. Although all documnetation and reports will be independent.
- Data: Seems to be initially email focused. Potentially tilts the project towards basic classification and scripting rather than nlp or record linkage. Actual brief given seems to disagree but will learn more when we get the data.
- Mis: Literature review reading list is still pending. AIP will send important note pertaining to IRP project plan. Will continue doing my own literature review untill then. Have Ken's contact details now so will communicate with him once we receive this.

## 06/06/25 Meeting With Yassine
Me, Ken and Yassine.

Discussed:
- Availabilty of data. General assumption is that it will have name, firm name and email address with potentially other data fields. Still haven't received actual data yet.
- Project Plan. Have been given sample plans to inform us on structure.
- Advised that pulling LLMs and finetuning them for our purposes could lead to a better product.
- It was made clear that the emphasis is creating a usable product for commercial purposes. Along side creating and proving the model.
- Can explore none model options for mapping company names to email domains.

Actions:
- Now that my literature review is done. Really time to get project plan done.
- If I get a draft in by Wednesday then I can get it reviewed.

# 20/06/25 Face to Face at Lansdowne
Me, Ken, Antony, Yassine, Other project teams.

Discussed:
- Missing Emails and complex names and therefore email templates. Anotny conveyed an understanding that edge cases will be inherently low confidence, can try to make robust with more robust pattern mining but if project is successfull for majority high coverage templates then that is valuable output.
- Domian mappings are important. Antony conveyed that the LP dataset should be largely exhaustive in terms of firms. It might be better to use websit to domain mappings, as there is more website records and different firms are subsidaries that use the same parent domain and website.
- Licensing for Third Party tools (Verification APIs). SMNP calls are the easiest but there may be cases where a more robust tool may be required to give us the confidence we require. Generally licensing shouldn't matter, especially since this is a research project but high cost APIs are obviously not ideal.
- A subset of data including hard bounce investor data is available and will be provided to us. This could be useful for validation to test our recovery on previously bounced attempts.
- Firms not in the dataset will be impossible to predict, AIP understand this.
- For stretch goals, if a contact cannot be found a side lookup for LinkedIn or any other contact detail will be valuable enrichment in lieu of high confidence email predictions. Tools like PhantomBuster.
- Expected workflow from user perspective {Predict <- Optional Validate}. This will inform end product design.

Actions:
- Look into third party APIs in more detail.
- Start pattern mining, examine coverage of domains.
- Would be interesting to see how many firms have websites associated with them in dataset.
- Potentially investigate seperate website to domain mappings pattern mining. Fallback to lookup table as dataset should contain all possible firms.
- Consider a second pass on low coverage or confidence template structures or domains in pattern mining with alternative names or other fields for edge cases (such as maiden names).

# 09/07/25 Meeting with Yves
Me, Ken and Yves

First one in a while. The AIP team are commuting so haven't had the time, should have a fact to face this week or the week after. 

Discussed:
- Issues with the data, bias towards larger firms effecting validation.
- Talked about the report, how we need to tell a story to make the project interesting. Highlighted the importance of the report and how it will determine the overall quality of the project.
- Discuessed current progress, mentioned my models performance and how it generally performs well but struggles with smaller firms and investors with non typical names.
- Yves mentioned that cultural naming conventions are an interesting aspect of the project. Suggested training seperate models for edge cases, this is interesting idea i would like to action.
- Yves suggested that we should try downsampling. We had mentioned that we were striving to upsample to padd out the low investor count firms for model performance.
- Discussed the importance of benchmarking since our accuracy metrics don't really mean anything without something to compare to. This could be a LLM RAG alternative which would be something interesting to investigate, even as a comparative study if that works out.
- Also discussed, from an end product perspective, how the use could help retrain the model. LightGBM needs the entire dataset to train on which makes things a little tricky but it's interesting idea as service.
- This could also be extended to prompt the user to query on names or firms that the model lacks knowledge of.

Actions:
- Continue upsampling. See how validation is affected.
- Move onto downsampling, see if removing the large firms positively affects the small firms.
- Validate on actual templates to further identify which templates work well and which don't.
- Isolate different data sets for different naming conventions and train on them instead. That way we can have different models for different name characteristics.
- Try LLM RAG even if its just for a benchmark.

# 25/07/25 Teams call with Antony
Me, Ken and Antony. Written late from notes i had jotted down but forgot to commit.

Discussed:
- Short call, discussed progress.
- AIP was happy to reimburse colab credits cost. This is good because there is too much data to train on my laptop.
- They were also happy to cover the cost of third party APIs.

# 30/07/25 Catch up With Ken and Yves
Me, Ken, Yves. Written late from notes i had jotted down but forgot to commit.

Discussed:
- Another short call, not much left to discuss at this stage.
- Need to quantify results. How much better is one unified model than two models split by name complexity.
- It is time to start writing a report draft.
- No personal voice is to be used in the write up.
- No future tense in the write up.
- Need to critique and really explain why the model has the results it has.

Actions:
- Will take a weighted average of model performance between standard and complex names for validation comparisson. All testing is done on both standard and complex namesets in both unified and split models.

# 21/08/25 Final IRP Call
Me, Ken and Antony.

Discussed:
- Current progress. Model performance, state of code.
- Discussed the writeup. Antony offered to provide a read through of the write up if I get it to him by Monday Morning.
- Mentioned the importance of talking about edge cases, highlight the potential weakness and how that could be improved in future work.
- Talked about the struggle around domain resolution.
- Discussed how tightly the model is tied to firms in training data.
- Antony suggested to talk about how to make the model more sophisticated in write up.
- Antony also offered some unlabeled GP data to have the model predict on to test deliverability.

Actions:
- Will finish the latest train, finish my results and conclusion sections of write up.
- Will take on Antony's adivce in write up.
- Will send the write up for review.
- Will also get some predictions done, will have to do this smartly considering the flakiness of domain resolution.
