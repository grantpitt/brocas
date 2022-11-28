import json
import os
import openai
import dotenv

dotenv.load_dotenv()


class Choice(object):

    def __init__(self, finish_reason, index, logprobs, text):
        self.finish_reason = finish_reason
        self.index = index
        self.logprobs = logprobs
        self.text = text

class Usage(object):

    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class ResponeObject(object):

    def __init__(self, choices, created, id, model, object, usage):
        self.choices = choices
        self.created = created
        self.id = id
        self.model = model
        self.object = object
        self.usage = usage
    
    def get_text(self, idx):
        return self.choices[idx].text

    def get_all_texts(self):
        return [x.text for x in self.choices]

class PrepText:
    
    def __init__(self):
        self.task = str()
        self.exemplars = list()
        self.text = str()
    
    def parse_prompt(self, first, file_name=None):
        f_text = str()
        if file_name is None:
            file_name = "./transcripts/prep_text/simple.txt" if first else "./transcripts/gpt3/test_user/simple_a.txt"
        else:
            file_name = f"./transcripts/{file_name.split('/')[0]}/prep_speech.txt"
        
        with open(file_name, 'r') as a:
            f_text = a.read()

        f_list = f_text.split('\n')
        for line in f_list:
            starts = lambda x: line.startswith(x)
            if starts("@task"):
                self.task = line[6:]
            elif starts("@exemplar"):
                self.exemplars.append(line[10:])
            elif starts("@end"):
                return


    def to_string(self):
        if self.task == "" or self.text == "":
            return None
        text = self.task
        return "{}\n\n{}\n\"{}\" <".format(
                self.task, 
                '\n'.join(self.exemplars), 
                self.text)

    def write_to_file(self, file_name=None):
        estr = ["@exemplar {}\n".format(exemplar) for exemplar in self.exemplars]
        if file_name is None:
            file_name = "test_user/simple_a"
        with open(f"./transcripts/gpt3/{file_name}.txt", 'w') as a:
            a.write("@task {}\n{}@exemplar \"{}\" <".format(self.task, ''.join(estr), self.text))

def clean_response(response, save_file=None):
    json_resp_str = json.dumps(response, indent=4)
    if save_file is not None:    
        if not os.path.isdir(f"./response_json/{save_file.split('/')[0]}"):
            os.mkdir(f"./response_json/{save_file.split('/')[0]}")

        with open(f"./response_json/{save_file}.json", 'w') as outfile:
            json.dump(json_resp_str, outfile)
    
    data = json.loads(json_resp_str)
    data['choices'] = [Choice(**c) for c in data['choices']]
    resp_obj = ResponeObject(**data)

    return resp_obj.get_all_texts()

class GPT3_Interfacer:

    def __init__(self, save_file=None):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.save_file = save_file

    def send_text(self, prompt):
        response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, temperature=0.7, max_tokens=256, n=4, stop=">")
        return clean_response(response, save_file=self.save_file)

    def predict(self, prompt):
        prompt = "Give the next words in the sentence:\n\"I am going\" <to town>\n\"" + prompt +"\" <"
        response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, temperature=0.7, max_tokens=5, n=4, stop=">")
        
        return clean_response(response, save_file=None)

        
def format_responses(responses):
    return [resp[:-1] if resp[-1] == '>' else resp for resp in responses]

def translate(text, first, file_name=None):
    prep_text = PrepText()
    prep_text.parse_prompt(first, file_name)
    prep_text.text = text.strip()
    prep_text.write_to_file(file_name)
    translator = GPT3_Interfacer("test_user/cup" if file_name is None else file_name)
    out_s = format_responses(translator.send_text(prep_text.to_string()))
    
    return out_s

def predict(text):
    predictor = GPT3_Interfacer()
    responses = predictor.predict(text.strip())
    out_s = format_responses(responses)
    return out_s

if __name__ == "__main__":
    translation = translate("I want buy a", True)
    print(translation[0])
    prediction = predict(translation[0])
    print(prediction)
