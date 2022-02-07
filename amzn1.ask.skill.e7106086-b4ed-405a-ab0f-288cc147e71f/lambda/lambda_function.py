# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
from ask_sdk_model import Response
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

import math

# start nltk

import boto3
from botocore.config import Config
from boto3.dynamodb.conditions import Key
import random

import string
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

nltk.data.path.append("/var/task/nltk_data")

# end nltk

# start persistance adapter 
import os
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

import requests
import json
#import sklearn.neighbors
#import numpy as np

ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')

ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)

# end persistance adapter 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

my_config = Config(
    region_name = 'eu-central-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10
    }
)

dietQuestions = [
    "Do you eat vegan, vegetarian or everything?", 
    "Can you please tell me if you are a vegan, vegetarian or meat eater?", 
    "Do you want to eat vegan, vegetarian or something with meat?"
]

timeQuestions = [
    "How much time do you have to cook?", 
    "How much time do you want to spend cooking?"
]

ingredientQuestions = [
    "Are there any specific ingredients you would like to use?", 
    "Do you want to use any specific ingredients?", 
    "Please tell me if there are any ingredients you would like to use."
]

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        logger.info("In LaunchIntentHandler")
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        # examples for using the dynamodb functions
        # currentTemperature = get_temperature(1)
        # currSeason = "summer"
        # ingredient1 = "olive oil"
        # ingredient2 = "garlic"
        # ingredient3 = "tomatoes"
        # currDiet = "vegetarian"
        # filteredRecipes = get_recipes_checked(5, 1000, currSeason, ingredient1, ingredient2, ingredient3, currDiet)
        # randomRecipe = get_random_recipe(filteredRecipes)
        # randomRecipeName = randomRecipe['name']
        # randomRecipeByName = get_recipe_by_name(randomRecipeName)
        # randomRecipeByNameID = randomRecipeByName['id']
    
        # type: (HandlerInput) -> Response

        speak_output = "Welcome to the cooking app. I will recommend the perfect recipe for you to cook. First, tell me a little bit about your day. How was it?"
        logger.info("temerature: " + str(get_temperature(1)))

        session_attr["weather"] = getWeather("Munich")
        session_attr["innerTemp"] = round(get_temperature(1))
        session_attr["season"] = calcSeason3(session_attr["innerTemp"], session_attr["weather"]["main"]["temp"], session_attr["weather"]["main"]["feels_like"])
        session_attr["ingredientOne"] = ""
        session_attr["ingredientTwo"] = ""
        session_attr["ingredientThree"] = ""


        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )




class SaveIntentHandler(AbstractRequestHandler):
    """Handler for Save Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SaveIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes

        # type: (HandlerInput) -> Response
        speak_output = ""

        slot = ask_utils.request_util.get_slot(handler_input, "text")

        if slot.value:
            logger.info(ask_utils.is_intent_name("TextSlot" + slot.value))

        ############## HERE INPUT TEMPERATURE SENSORE VALUE ###############

        TemperatureDegreeValue = round(get_temperature(1))
        dishTemperatureCategory = ""
        weatherDescription = ""

        if (TemperatureDegreeValue > 20):                       # -> summer dish
            dishTemperatureCategory = "refreshing"
            weatherDescription = "hot"
        elif (TemperatureDegreeValue > 10):                     # -> spring dish
            dishTemperatureCategory = "cool"
            weatherDescription = "warm"
        elif (TemperatureDegreeValue > 5):                      # -> fall dish
            dishTemperatureCategory = "warm"
            weatherDescription = "rather cold"
        else:                                                   # -> winter dish
            dishTemperatureCategory = "warming up"
            weatherDescription = "cold"

        ############## NLP USING NTLK ###############

        text = slot.value
        lower_case = text.lower()
        cleaned_text = lower_case.translate(
            str.maketrans('', '', string.punctuation))
        sentiment = "null"

        # Using word_tokenize because it's faster than split()
        tokenized_words = word_tokenize(text, "english")
        final_words = []

        for word in tokenized_words:
            if word not in stopwords.words('english'):
                final_words.append(word)

        # Lemmatization - From plural to single + Base form of a word (example better-> good)
            lemma_words = []
            for word in final_words:
                word = WordNetLemmatizer().lemmatize(word)
                lemma_words.append(word)

        def sentiment_analyse(sentiment_text):
            score = SentimentIntensityAnalyzer().polarity_scores(sentiment_text)
            if score['neg'] > score['pos']:
                #print("Negative Sentiment")
                a = 0
                return a
            elif score['neg'] < score['pos']:
                #print("Positive Sentiment")
                a = 1
                return a
            else:
                #print("Neutral Sentiment")
                a = 2
                return a

        # checks if slot has value and intro was already spoken
        if slot.value and "introSpoken" not in session_attr:
            sentiment = sentiment_analyse(cleaned_text)
            # sentiment == 0 -> Negativ,   sentiment == 1 -> Positiv,  sentiment == 2 -> Neutral
            speak_output = ""
            # Negativ
            if(sentiment == 0):
                session_attr["mood"] = -1
                speak_output = "Oh I'm sorry to hear that. In this case I will suggest a recipe that is easy and fast to lighten up your mood."

            # Positiv
            if(sentiment == 1):
                session_attr["mood"] = 1
                speak_output = "That sounds great! In this case I will suggest a recipe that is delicious and can take some more steps to cook."

            # Neutral
            if(sentiment == 2):
                session_attr["mood"] = 0
                speak_output = "Okay, sounds like you had quite the normal day. In this case I will suggest a recipe with mediocre effort."

            speak_output += " Now, let's first check the weather conditions. Using my temperature sensore I can say that it is " + \
                str(TemperatureDegreeValue) + " degrees inside. Therefore I will look for " + dishTemperatureCategory + " dishes that suit today's rather " + \
                weatherDescription + \
                " temperature inside. "
            speak_output += random.choice(ingredientQuestions)
            
            #once the intro is spoken introSpoken will be true --> intro will not be repeated
            session_attr["introSpoken"] = "true"

        else: 
            #ResponseHandler handles questions to be asked 
            speak_output = ResponseHandler(handler_input)

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


#gets triggered if speaks out one or more ingredients
#ingredients get saved in session attributes
class IngredientIntentHandler(AbstractRequestHandler):
    """Handler for Attributes Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("IngredientIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In IngredientIntentHandler")
        ingredientOneSlot = ask_utils.request_util.get_slot(handler_input, "ingredientOne")
        ingredientTwoSlot = ask_utils.request_util.get_slot(handler_input, "ingredientTwo")
        ingredientThreeSlot = ask_utils.request_util.get_slot(handler_input, "ingredientThree")

        session_attr = handler_input.attributes_manager.session_attributes
         
        if ingredientOneSlot and ingredientOneSlot.value:
            session_attr["ingredientOne"] = ingredientOneSlot.value

        if ingredientTwoSlot and ingredientTwoSlot.value:
            session_attr["ingredientTwo"] = ingredientTwoSlot.value

        if ingredientThreeSlot and ingredientThreeSlot.value:
            session_attr["ingredientThree"] = ingredientThreeSlot.value

        #ResponseHandler handles questions to be asked 
        speak_output = ResponseHandler(handler_input)

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

#gets triggered if speaks out a diet
#diet gets parsed and saved in session and persistant attributes ('vegan', 'vegetarian' or 'meat')
class DietIntentHandler(AbstractRequestHandler):
    """Handler for Attributes Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DietIntent")(handler_input)

    def handle(self, handler_input):

        dietSlot = ask_utils.request_util.get_slot(handler_input, "diet")

        session_attr = handler_input.attributes_manager.session_attributes
        pers_attr = handler_input.attributes_manager.persistent_attributes

        #parse diet slot
        if dietSlot.value:
            diet = dietSlot.value
            if (diet =="vegan" or diet =="do not eat diaries" or diet =="diary-free" or diet =="don't eat diaries" or diet =="no diaries"):
                session_attr["diet"] = "vegan"
            elif(diet =="vegetarian" or diet =="do not eat meat" or diet =="don't eat meat" or diet =="no meat"): 
                session_attr["diet"] = "vegetarian"
            elif(diet =="with meat" or diet =="eat meat" or diet =="everything" or diet =="meat eater"): 
                session_attr["diet"] = "meat"

            #save diet in persistent attributes for future sessions
            if("diet" in session_attr): 
                pers_attr['diet'] = session_attr["diet"]
                handler_input.attributes_manager.save_persistent_attributes()



        #ResponseHandler handles questions to be asked 
        speak_output = ResponseHandler(handler_input)

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

#gets triggered if speaks out a specific or unspecific cooking time
#specific cooking time gets parsed in minutes and saved in session attributes
#unspecific cooking time gets parsed in minutes and saved in session attributes ('30', '120' or '1000')
class TimeIntentHandler(AbstractRequestHandler):
    """Handler for Attributes Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TimeIntent")(handler_input)

    def handle(self, handler_input):

        timeSlot = ask_utils.request_util.get_slot(handler_input, "time")
        unspecificTimeSlot = ask_utils.request_util.get_slot(handler_input, "unspecificTime")

        session_attr = handler_input.attributes_manager.session_attributes

        #parse time slot to minutes
        if timeSlot.value:
            time = timeSlot.value
            res = time[2:len(time)]
            mins = 0
            timelist = res.split("H")
            if(len(timelist) > 1):
                mins = +int((int(timelist[0])*60))
                if(timelist[1]): 
                    mins += int((timelist[1][0: (len(timelist[1])-1)]))
            else: 
                mins = res[0: (len(res)-1)]

            session_attr["minTime"] = str(int(mins)-15)
            session_attr["maxTime"] = str(mins)

        #parse unspecific time slot to minutes
        if unspecificTimeSlot.value:
            time = unspecificTimeSlot.value
            if (time =="not much time" or time =="as little as possible" or time =="make it quick" or time =="keep it short" or time =="quick" or time =="little time" or time == "fast"):
                if "mood" in session_attr and (session_attr["mood"] == -1): 
                    session_attr["maxTime"] = "20"
                elif "mood" in session_attr and (session_attr["mood"] == 1): 
                    session_attr["maxTime"] = "40"
                else: 
                    session_attr["maxTime"] = "30"
            elif (time =="much time" or time =="a lot of time" or time =="a lot"):
                if "mood" in session_attr and (session_attr["mood"] == -1): 
                    session_attr["minTime"] = "30"
                    session_attr["maxTime"] = "90"
                elif "mood" in session_attr and (session_attr["mood"] == 1): 
                    session_attr["minTime"] = "60"
                    session_attr["maxTime"] = "180"
                else:
                    session_attr["minTime"] = "45"
                    session_attr["maxTime"] = "120"
            elif (time =="don't care" or time =="don't know"):
                session_attr["maxTime"] = "1000000"
            
        speak_output = ResponseHandler(handler_input)

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

#handles all the speak_output
#checks if user already answerd diet and time and asks for values if they were not already given
#if alle required values were filled a matching recipe will be suggested
def ResponseHandler(handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        pers_attr = handler_input.attributes_manager.persistent_attributes
        speak_output = ""

        if ("diet" in pers_attr) and ("diet" not in session_attr):
            speak_output += "You eat " + pers_attr["diet"] + ", right? "
        elif ("diet" not in session_attr) and ("diet" not in pers_attr): 
            speak_output += random.choice(dietQuestions)
        elif "maxTime" not in session_attr:
            speak_output += random.choice(timeQuestions)
        elif "suggestedRecipe" in session_attr:
            speak_output += GetSuggestion(session_attr)
        else: 

            #if user filled all required slots a filtered list with recipes will be generated
            filteredRecipes = GetFilteredRecipes(handler_input)

            session_attr["recommendedRec"] = []
            session_attr["notRecommendedRec"] = []

            #define which recipes get recommended
            #the recipes which do not get recommended will be saved as backup in "notRecommendedRec" and will be suggested if all recommended recipes get declined by the user
            for x in filteredRecipes:
                if (recommender(x, handler_input)): 
                    session_attr["recommendedRec"].append(x)
                    logger.info("Another recipe "+str(len(filteredRecipes)))
                else: 
                    session_attr["notRecommendedRec"].append(x)
            
            speak_output = GetSuggestion(session_attr)
        
        return speak_output


def GetSuggestion(session_attr): 
    speak_output = ""
    filteredRecipes = []

    #recommended recipes get suggested first. If the user does not accept any of them, the not recommended recipes gets suggested
    if(("recommendedRec" in session_attr) and len(session_attr["recommendedRec"]) > 0): 
        filteredRecipes = session_attr["recommendedRec"]
    elif (("notRecommendedRec" in session_attr) and len(session_attr["notRecommendedRec"]) > 0): 
        filteredRecipes = session_attr["notRecommendedRec"]
    

    if(len(filteredRecipes) > 0): 
        suggestedRecipe = random.choice(filteredRecipes)
        session_attr["suggestedRecipe"] = suggestedRecipe
        speak_output = "Do you want to cook " + get_name(suggestedRecipe) + "? It will take about " + str(get_minutes(suggestedRecipe)) + " minutes."
    else: 
        speak_output = "Sorry, I can't find anything matching your requirements"
    
    return speak_output


class YesIntentHandler(AbstractRequestHandler):
    """Handler for Attributes Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In YesIntentHandler")

        session_attr = handler_input.attributes_manager.session_attributes
        pers_attr = handler_input.attributes_manager.persistent_attributes


        if "suggestedRecipe" in session_attr: 
            SaveUserFeedback(1, handler_input) 
            speak_output = "I'm happy I was able to help. Happy cooking!"
        else: 
            if ("diet" in pers_attr) and ("diet" not in session_attr):
                session_attr["diet"] = pers_attr["diet"]
            speak_output = ResponseHandler(handler_input)


        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class NoIntentHandler(AbstractRequestHandler):
    """Handler for Attributes Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In NoIntentHandler")

        session_attr = handler_input.attributes_manager.session_attributes

        if "suggestedRecipe" in session_attr: 
            #if user declines recipe it will be deleted and not suggested anymore
            for x in session_attr["recommendedRec"]:
                if(get_id(session_attr["suggestedRecipe"]) == get_id(x)):
                    session_attr["recommendedRec"].remove(x)
            
            for x in session_attr["notRecommendedRec"]:
                if(get_id(session_attr["suggestedRecipe"]) == get_id(x)):
                    session_attr["notRecommendedRec"].remove(x)

            SaveUserFeedback(0, handler_input)         
        speak_output = ResponseHandler(handler_input)

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

def SaveUserFeedback(feedback, handler_input): 
    session_attr = handler_input.attributes_manager.session_attributes

    #   NEW     #
    # Get the Data of the Recommender History 
    data_2_AlreadyEvaluatedRecipes = requests.get("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"})
    # convert JSON in PY
    jsonresponse_2 = data_2_AlreadyEvaluatedRecipes.text
    data_2 = json.loads(jsonresponse_2)
    logger.info("send_data 2 season ="+str(session_attr["season"]))

    #   NEW     #
    currentdata_string = '{"'+str(len(data_2))+'":{"Season": "'+ str(session_attr["season"]) +'", "Stresslevel": '+ str(session_attr["mood"]) +', "Ingredients": { "0" : "'+ str(session_attr["ingredientOne"]) +'", "1": "'+ str(session_attr["ingredientTwo"]) +'", "2": "'+ str(session_attr["ingredientThree"]) +'"}, "RecommendedRecipeID": '+ str(get_id(session_attr["suggestedRecipe"])) +', "Rating": '
    
    #   NEW     #
    currentdata_string += str(feedback) + "} }"

    logger.info("Upload String:" + currentdata_string)

    #Update data_2
    currentdata = json.loads(currentdata_string)
    
    data_2.update(currentdata)
    data_2_upload = json.dumps(data_2)
    send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=data_2_upload)



#print("In "+city+": Real Temp: "+str(weatherdata["main"]["temp"])+", Feels like: "+str(weatherdata["main"]["feels_like"]))
def CommunicateSuggestions(totest, handler_input):
    #totest = ["A","B","C","D","E","F","G","H"]
    session_attr = handler_input.attributes_manager.session_attributes
    recommenderdeclined = []
    while(len(totest)>0):

        #   NEW     #
        # Get the Data of the Recommender History 
        data_2_AlreadyEvaluatedRecipes = requests.get("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"})
        # convert JSON in PY
        jsonresponse_2 = data_2_AlreadyEvaluatedRecipes.text
        data_2 = json.loads(jsonresponse_2)


        pos = random.randint(0, len(totest)-1)
        #Recommender Funktion
        #torecommend = ReccomenderDummy(totest[pos])
        torecommend = recommender(totest[pos], handler_input)
        logger.info("recommended: " + str(torecommend))
        if(torecommend):

             #   NEW     #
            currentdata_string = '{"'+str(len(data_2))+'":{"Season": '+ str(session_attr["season"]) +', "Stresslevel": '+ str(session_attr["mood"]) +', "Ingredients": { "0" : "'+ str(session_attr["ingredientOne"]) +'", "1": "'+ str(session_attr["ingredientTwo"]) +'", "2": "'+ str(session_attr["ingredientThree"]) +'"}, "RecommendedRecipeID": '+ str(totest[pos].id) +', "Rating": '
           
            logger.info("Rec Accept "+str(totest[pos]))
            useracceptance = UserFeedbackDummy(1)
            # useracceptance = UserFeedback(totest[pos])
            if(useracceptance):
                #Done and write feedback to RecommenderDB
                logger.info("User Accepted")

                #   NEW     #
                currentdata_string += "1} }"
                #Update data_2
                currentdata = json.loads(str(currentdata_string))
                data_2.update(currentdata)
                data_2_upload = json.dumps(data_2)
                logger.info("Upload String:" +data_2_upload)
                send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=data_2_upload)


                return "Great, happy cooking"
            else:
                #write Feedback to RecommenderDB
                logger.info("User Declined")

                #   NEW     #
                currentdata_string += "0} }"
                #Update data_2
                print(currentdata_string)
                currentdata = json.loads(currentdata_string)
                data_2.update(currentdata)
                data_2_upload = json.dumps(data_2)
                logger.info("Upload String:" +data_2_upload)
                send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=data_2_upload)

                del totest[pos]
        else:
            logger.info("Rec Declined "+str(totest[pos]))
            recommenderdeclined.append(totest[pos])
            del totest[pos]
    for x in recommenderdeclined:

        #   NEW     #
        # Get the Data of the Recommender History 
        data_2_AlreadyEvaluatedRecipes = requests.get("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"})
        # convert JSON in PY
        jsonresponse_2 = data_2_AlreadyEvaluatedRecipes.text
        data_2 = json.loads(jsonresponse_2)
        currentdata_string = '{"'+str(len(data_2))+'":{"Season": '+ str(session_attr["season"]) +', "Stresslevel": '+ str(session_attr["mood"]) +', "Ingredients": { "0" : "'+ str(session_attr["ingredientOne"]) +'", "1": "'+ str(session_attr["ingredientTwo"]) +'", "2": "'+ str(session_attr["ingredientThree"]) +'"}, "RecommendedRecipeID": '+ str(totest[pos].id) +', "Rating": '
           
        useracceptance = UserFeedbackDummy(1)
        # useracceptance = UserFeedback(x)
        if(useracceptance):
            #Done and write feedback to RecommenderDB
            logger.info("User Accepted "+str(x))

            #   NEW     #
            currentdata_string += "1} }"
            #Update data_2
            currentdata = json.loads(currentdata_string)
            data_2.update(currentdata)
            data_2_upload = json.dumps(data_2)
            print("Upload String:" +data_2_upload)
            send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=data_2_upload)


            return "Great, happy cooking"
        else:
            #write Feedback to RecommenderDB
            logger.info("User Declined "+str(x))

            #   NEW     #
            currentdata_string += "0} }"
            #Update data_2
            currentdata = json.loads(currentdata_string)
            data_2.update(currentdata)
            data_2_upload = json.dumps(data_2)
            print("Upload String:" +data_2_upload)
            send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=data_2_upload)

    return "Sorry, I can not find anything"



# # Link to manualy update FIRST JSON Bin with one recipe proposal: https://extendsclass.com/jsonstorage/e6034bd4f80a
# # Link to manualy update SECOND JSON Bin with already evaluated recipes: https://extendsclass.com/jsonstorage/0c935554f82d
# Get Data
# data_1_RecipeProposal=requests.get("https://json.extendsclass.com/bin/e6034bd4f80a", headers={"Security-key":"IUI"})

# Get Data from already rated recipes
data_2_AlreadyEvaluatedRecipes = requests.get("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"})

# # convert JSON in PY
# jsonresponse_1 = data_1_RecipeProposal.text
# data_1 = json.loads(jsonresponse_1)

jsonresponse_2 = data_2_AlreadyEvaluatedRecipes.text
data_2 = json.loads(jsonresponse_2)

# # Recommender Weights
Season_Weight = 10
Ingredient_weight = 10  # 1 or 0
Stresslevel_weight = 10 # 0 (neg) or 1 (neutral) or 2 (pos)


# example JSON:
#{
#	"Season": 1,
#	"Stresslevel": 0,
#	"Ingredients": {
#		"0": "tomatoe",
#		"1": "potato", 
#        "2": "kiwi"
#	},
#	"RecommendedRecipeID": 1
#}



def euclidean_distance(row1, row2):
	distance = float(0.0)
	for i in range(len(row1)):
		distance += (float(row1[i]) - float(row2[i]))**2
	return math.sqrt(distance)


# Recommender function
def recommender(recipe, handler_input): 
    session_attr = handler_input.attributes_manager.session_attributes

    logger.info(session_attr["season"])
    Accepted = False

    recipe_list = [] # list with all the entries where the same recipeID has been selected and rated
    Similarity_Values_list = [] # list with all the entries of recipes that were rated

     # first save all entries where the same recipeID has been selected and rated
    for v in data_2.values():
        if(get_id(recipe) == v['RecommendedRecipeID']):
            recipe_list.append(v)

    if recipe_list: 
        # list is not empty, take average rating of all the times the user rated this recipe
        sum = 0
        for index in recipe_list:
            sum += index["Rating"]
        avg_Rating = sum/len(recipe_list) 
        print(avg_Rating)
        Accepted = avg_Rating > 0.5 # Hardcoded Value (?) Ratings are 0 for not accepted by user and 1 for accepted by user -> do not recommend with ratings underneath 0.5
        if(Accepted):
            return Accepted
        
    if (not Accepted or not recipe_list):
        # check for similarities in all entries 
        ingredientsCount = get_number_of_ingredients(recipe)  #number of ingredients in recommended recipe
        # logger.info(ingredientsCount)
        for v in data_2.values():
            ingredientsValue = 0 # how many ingredients are the same
            ingredients = get_ingredients(recipe)
            #logger.info("ingredients = ")
            #logger.info(ingredients)
            
            ingredientList = ingredients.split(',')
            ingList = []
            
            for element in ingredientList:
                ingList.append(element[1:-1].replace("'",""))
            for ing1 in ingList:
                        for ing2 in v['Ingredients']:
                            if (v['Ingredients'][ing2].lower() == ing1.lower()):
                                    ingredientsValue += 1
                                    #logger.info("save "+ str(ingredientsValue) +str(ing1.lower()) + ", "+ str(v['Ingredients'][ing2].lower()))
       
            Similarity_Values_list.append([int(v['Season']) * Season_Weight,  v['Stresslevel'] * Stresslevel_weight, ingredientsValue * Ingredient_weight]) 
                    
        # Calculate nearest neighbor using the nearest neighbor approach
        #model = sklearn.neighbors.NearestNeighbors(n_neighbors = 1, algorithm = 'brute', metric='cosine')
        #model.fit(Similarity_Values_list)
        counter = 0
        MinValueIndex = 0
        MinDistance = 1000

        recipeToCompareTo = [ int(session_attr["season"]) *Season_Weight, session_attr["mood"] *Stresslevel_weight, ingredientsCount * Ingredient_weight]
        # Calculate nearest neighbor using the euclidian distance
        for entry in Similarity_Values_list:
            #logger.info(str(entry))
            #logger.info(str(recipeToCompareTo))
            dist = euclidean_distance(entry, recipeToCompareTo)
            #print("Distance entry "+ str(counter) +" = "+str(dist))
            if(dist < MinDistance):
                MinDistance = dist
                MinValueIndex = counter
                #logger.info("counter = "+str(counter)+", MinDistance = "+str(MinDistance)+", MinValueIndex = "+str(MinValueIndex))
            counter += 1

        #logger.info(Similarity_Values_list)
        #logger.info("closest recipe is "+ str(MinValueIndex) + "with a distance of "+ str(MinDistance))
        suggestion_index = str(int(MinValueIndex))
        #recipe2 = np.array([ session_attr["season"] *Season_Weight, session_attr["mood"] *Stresslevel_weight, ingredientsCount * Ingredient_weight])

        #logger.info(recipe2)
        #distance, suggestion = model.kneighbors((np.reshape(recipe, (1,-1))))
        #suggestion_index = "0"
        
        #logger.info(data_2[suggestion_index]['RecommendedRecipeID'])

        #Accepted = data_2[suggestion_index]['Rating'] > 0.5
#        print("distance = "+str(distance[0]))

        if (int(MinDistance) >= 100): # meaning the next closest recipe to the proposal is still quite far off, accept it 
            Accepted = True    #default is true
        else: # check for the recommendation on the closest recipe
            Accepted = data_2[suggestion_index]['Rating'] > 0.5

        return Accepted   


# if(Accepted):
#     print("The proposed recipe is accepted. Ask the user to rate how much they like the proposal from 1 to 10.")
#     #TODO Alexa: ask user for the rating of the proposed recipe
#     rating = -1

#     #Convert PY in JSON
#     index = len(list(data_2.values()))
#     entry = {"TemperatureI": data_1["TemperatureI"], "TemperatureO": data_1["TemperatureO"], "Stresslevel": data_1["Stresslevel"], "Ingredients": data_1["Ingredients"], "RecommendedRecipeID": data_1["RecommendedRecipeID"], "Rating": rating}
#     data_2[index] = entry
#     jsfrompy = json.dumps(data_2)
    
#     #Send updated Data back to JSON Bin
#     send_data_2 = requests.put("https://json.extendsclass.com/bin/0c935554f82d", headers={"Security-key":"IUI"}, data=jsfrompy)

# else:
#     print("The proposed recipe is not accepted. Get another proposal from the database.")

def ReccomenderDummy(id):
    if(random.randint(0,3)==0):
        return True
    return False 

def UserFeedbackDummy(id):
    if(random.randint(0,3)==0):
        return True
    return False

#For Inside, Outside and feel-Outside Temperature (tempinside , tempoutside , tempoutside_feel)
def calcSeason3(tempinside, tempoutside, tempoutside_feel):
    deltafeel = tempoutside-tempoutside_feel
    deltainout=tempinside-tempoutside
    if(tempinside < 18 and tempoutside_feel<10):
        return 1

    if((deltainout<0 and deltafeel<0) or (tempoutside_feel>24)):
        return 4

    if((deltainout<8 and tempoutside>10) or (deltainout<8 and deltafeel<=0)):
        return 3

    if((deltainout<15 and tempoutside>3) or (deltainout<15 and deltafeel>0)):
        return 2

    return 1


#For Inside and Outside Temperature (tempinside , tempoutside )
def calcSeason2(tempinside, tempoutside):
    tempdelta = tempinside - tempoutside
    if(tempinside < 18):
        return 0

    if(tempdelta<0):
        return 2

    if(tempdelta<8 and tempoutside>10):
        return 1

    if(tempdelta<15 and tempoutside>3):
        return 3

    return 0


#For Outside Temperature only
def calcSeason1(temp):
    if(temp>23):
        return 2

    if(temp>14):
        return 1

    if(temp>5):
        return 3

    return 0 


#Weather Stuff
def getWeather(city):
    r_w = requests.get("https://api.openweathermap.org/data/2.5/weather?q="+city+"&units=metric&appid=21471eb4a684cb275a160b3005639585")
    jsonresponse_w = r_w.text
    weatherdata = json.loads(jsonresponse_w)
    return(weatherdata)


#TODO: include season/temerature attribute in recipe request
#returns a recipe with matching the users input (time, diet, ingredients)
def GetFilteredRecipes(handler_input): 
        session_attr = handler_input.attributes_manager.session_attributes
        currSeason = "summer"
        ingredient1 = ""
        ingredient2 = ""
        ingredient3 = ""
        currDiet = "meat"
        maxTime = 1000
        minTime = 0
        minSteps = 2
        maxSteps = 9

        if "maxTime" in session_attr: 
            maxTime =  int(session_attr["maxTime"])
        if "minTime" in session_attr: 
            minTime = int(session_attr["minTime"])
        if "diet" in session_attr: 
            currDiet = session_attr["diet"]
        if "ingredientOne" in session_attr: 
            ingredient1 = session_attr["ingredientOne"]
        if "ingredientTwo" in session_attr: 
            ingredient2 = session_attr["ingredientTwo"]
        if "ingredientThree" in session_attr: 
            ingredient3 = session_attr["ingredientThree"]
        if "season" in session_attr: 
            if session_attr["season"] == 1: 
                currSeason = "winter"
            if session_attr["season"] == 2:
                currSeason = "fall"
            if session_attr["season"] == 3:
                currSeason = "spring"
            if session_attr["season"] == 4:
                currSeason = "summer"
        if "mood" in session_attr:
            if session_attr["mood"] == -1: 
                minSteps = 0
                maxSteps = 7
            if session_attr["mood"] == 1: 
                minSteps = 4
                maxSteps = 20

        filteredRecipes = get_recipes_checked(minTime, maxTime, currSeason, ingredient1, ingredient2, ingredient3, currDiet, minSteps, maxSteps)
        if(len(filteredRecipes)>50):
            filteredRecipes = filteredRecipes[:50]
        # recipe = random.choice(filteredRecipes)
        # session_attr["recipeId"] = str(get_id(recipe))
        return filteredRecipes


#connects to niklas' aws accounts dynamodb
#returns a dynamodb instance
def connect_dynamodb():
    sts_client = boto3.client('sts', config=my_config)
    assumed_role_object=sts_client.assume_role(RoleArn="arn:aws:iam::629610792425:role/temperatureGetter", RoleSessionName="temperatureGetter")
    credentials=assumed_role_object['Credentials']

    dynamodb = boto3.resource('dynamodb',
                  aws_access_key_id=credentials['AccessKeyId'],
                  aws_secret_access_key=credentials['SecretAccessKey'],
                  aws_session_token=credentials['SessionToken'],
                  region_name='eu-central-1')
    return dynamodb

#gets the last temperature entry that has been written to the dynamodb table by the raspberry pi sensor with the measurementDeviceID (currently we only have one raspberry with the id 1)
#returns the temperature as a decimal
def get_temperature(measurementDeviceID):
    dynamodb = connect_dynamodb()
    measurement = dynamodb.Table('Temperatur_Values').query(KeyConditionExpression=Key('measurementDeviceID').eq(measurementDeviceID), ScanIndexForward=False, Limit=1)['Items']
    measurementParsed = measurement[0]
    return measurementParsed['temperature']

#returns the recipe with the id recipeID as a json-like object
def get_recipe_by_id(recipeID):
    dynamodb = connect_dynamodb()
    recipesTable = dynamodb.Table('Recipes')
    recipe = recipesTable.query(KeyConditionExpression=Key('id').eq(recipeID))['Items']
    recipeParsed = recipe[0]
    return recipeParsed

#returns a python list of recipes that have the specified season in the tags
def get_recipes_by_season(season):
    dynamodb = connect_dynamodb()
    recipesTable = dynamodb.Table('Recipes')
    
    #for scanning the whole database:
    response = recipesTable.scan(FilterExpression="contains(#tags, :v)", ExpressionAttributeNames={ "#tags": "tags" }, ExpressionAttributeValues={ ":v": season })
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], FilterExpression="contains(#tags, :v)", ExpressionAttributeNames={ "#tags": "tags" }, ExpressionAttributeValues={ ":v": season })
        data.extend(response['Items'])
    return data

#returns a recipe with the specified name if it exists, otherwise it returns the "rumtopf" recipe. This "error handling" should be just temporary
# def get_recipe_by_name(name):
#     dynamodb = connect_dynamodb()
#     recipesTable = dynamodb.Table('Recipes')
    
#     response = recipesTable.scan(FilterExpression="contains(#name, :name)", ExpressionAttributeNames={ "#name": "name" }, ExpressionAttributeValues={ ":name": name })
#     data = response['Items']
#     while 'LastEvaluatedKey' in response:
#         response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], FilterExpression="contains(#name, :name)", ExpressionAttributeNames={ "#name": "name" }, ExpressionAttributeValues={ ":name": name })
#         data.extend(response['Items'])
#     if len(data) not 0:
#         return data[0]
#     else:
#         return get_recipe_by_id(12931)

#returns a python list of recipes in a json-like object that have the specified season and diet in the tags
def get_recipes_by_season_and_diet(season, diet):
    dynamodb = connect_dynamodb()
    recipesTable = dynamodb.Table('Recipes')
    
    response = recipesTable.scan(FilterExpression="contains(#tags, :v1) and contains(#tags, :v2)", ExpressionAttributeNames={ "#tags": "tags", "#tags": "tags" }, ExpressionAttributeValues={ ":v1": season, ":v2": diet })
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], FilterExpression="contains(#tags, :v1) and contains(#tags, :v2)", ExpressionAttributeNames={ "#tags": "tags", "#tags": "tags" }, ExpressionAttributeValues={ ":v1": season, ":v2": diet })
        data.extend(response['Items'])
    return data

#returns a python list of recipes with a prepatation time (db key: minutes) between minTime and maxTime
def get_recipes_by_time(minTime, maxTime):
    dynamodb = connect_dynamodb()
    recipesTable = dynamodb.Table('Recipes')
    response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime", ExpressionAttributeNames={"#minutes": "minutes"}, ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime})
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
        FilterExpression="#minutes BETWEEN :minTime AND :maxTime", ExpressionAttributeNames={"#minutes": "minutes"}, ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime})
        data.extend(response['Items'])
    return data

#minTime, maxTime and season must NOT be None; ingredient1, ingredient2, ingredient1 and diet can be None when calling this function
#returns a python list of recipes
#this function stepwise reduces the amount of specified parameters if no fitting recipe has been found
def get_recipes_checked(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max):
    logger.info("minTime: " + str(minTime))
    logger.info("maxTime: " + str(maxTime))
    logger.info("season: " + season)
    logger.info("ingredient1: " + ingredient1)
    logger.info("ingredient2: " + ingredient2)
    logger.info("ingredient3: " + ingredient3)
    logger.info("diet: " + diet)
    logger.info("n_steps_min: " + str(n_steps_min))
    logger.info("n_steps_max: " + str(n_steps_max))
    recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
    if len(recipesList) < 8:
        ingredient3 = ""
        logger.info("ingredient3 now empty")
        recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
        if len(recipesList) < 8:
            ingredient2 = ""
            logger.info("ingredient2 now empty")
            recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
            if len(recipesList) < 8:
                ingredient1 = ""
                logger.info("ingredient1 now empty")
                recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
                if len(recipesList) < 8:
                    n_steps_min = 0
                    n_steps_max = 1000
                    logger.info("number of steps neutralized")
                    recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
                    if len(recipesList) < 8:
                        minTime = 15
                        maxTime = 120
                        logger.info("time neutralized")
                        recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
                        if len(recipesList) < 8:
                            diet = "meat"
                            logger.info("diet neutralized")
                            recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
                            if len(recipesList) < 8:
                                season = "summer"
                                logger.info("len(recipesList) " + str(len(recipesList)))
                                logger.info("season neutralized")
                                recipesList = get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max)
                                logger.info("len(recipesList) " + str(len(recipesList)))
    return recipesList

#minTime, maxTime, season, diet, n_steps_min and n_steps_max must NOT be None; ingredient1, ingredient2, ingredient3 can be None when calling this function
#returns a python list of recipes filtered by the specified parameters
#depending on which parameters have been set, different database scans are executed
def get_recipes(minTime, maxTime, season, ingredient1, ingredient2, ingredient3, diet, n_steps_min, n_steps_max):
    dynamodb = connect_dynamodb()
    recipesTable = dynamodb.Table('Recipes')
    
    if ingredient1=="" and diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data
        #for scanning only the first megabyte of the table
        #return recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue)", \
        #ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags"}, \
        #ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season})['Items'] 

    if ingredient1=="" and not diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and ingredient2=="" and diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and ingredient2=="" and not diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and not ingredient2=="" and ingredient3=="" and diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and not ingredient2=="" and ingredient3=="" and not diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and not ingredient2=="" and not ingredient3=="" and diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and contains(#ingredients, :ingredient3) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":ingredient3": ingredient3, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and contains(#ingredients, :ingredient3) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":ingredient3": ingredient3, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

    if not ingredient1=="" and not ingredient2=="" and not ingredient3=="" and not diet=="meat":
        response = recipesTable.scan(FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and contains(#ingredients, :ingredient3) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
        ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
        ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":ingredient3": ingredient3, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = recipesTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], \
            FilterExpression="#minutes BETWEEN :minTime AND :maxTime and contains(#tags, :seasonValue) and contains(#tags, :dietValue) and contains(#ingredients, :ingredient1) and contains(#ingredients, :ingredient2) and contains(#ingredients, :ingredient3) and #n_steps BETWEEN :n_steps_min AND :n_steps_max", \
            ExpressionAttributeNames={"#minutes": "minutes", "#tags": "tags", "#ingredients": "ingredients", "#n_steps": "n_steps"}, \
            ExpressionAttributeValues={":minTime": minTime, ":maxTime": maxTime, ":seasonValue": season, ":dietValue": diet, ":ingredient1": ingredient1, ":ingredient2": ingredient2, ":ingredient3": ingredient3, ":n_steps_min": n_steps_min, ":n_steps_max": n_steps_max})
            data.extend(response['Items'])
        return data

#returns a random recipe from a given list of recipes. The parameter recipes must be a python list as returned by e.g. get_recipes_checked() 
def get_random_recipe(recipes):
    return recipes[random.randint(0, len(recipes))]

def get_number_of_steps(recipe):
    return recipe['n_steps']

def get_number_of_ingredients(recipe):
    return recipe['n_ingredients']

def get_nutrition(recipe):
    return recipe['nutrition']

def get_minutes(recipe):
    return recipe['minutes']

def get_number(recipe):
    return recipe['number']

def get_steps(recipe):
    return recipe['steps']

def get_description(recipe):
    return recipe['description']

def get_ingredients(recipe):
    return recipe['ingredients']

def get_id(recipe):
    return recipe['id']

def get_name(recipe):
    return recipe['name']

def get_tags(recipe):
    return recipe['tags']

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open for the user to respond")
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


# sb = SkillBuilder()
sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(DietIntentHandler())
sb.add_request_handler(TimeIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(IngredientIntentHandler())
sb.add_request_handler(SaveIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
