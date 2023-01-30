from datetime import datetime
import pandas as pd

def get_score(array, label_values):
        
    # calculate score based on classes and labels
    labels = array[0].split(' ')
    labels_score = sum([label_values[i] for i in labels if i in label_values.keys()])
    
    # calculate score based on age of the email
    email_intime = pd.to_datetime(array[3])
    total_days = (datetime.now() - email_intime).days
    time_score = total_days * (15/365)
    
    #calculate score based on size of the email
    size_score = array[2] * (0.00001)
    
    total_score = labels_score + time_score + size_score
    
    return total_score    
        
# Driver Code to calculate the score of one email request

a = ['UNREAD IMPORTANT CATEGORY_FORUMS TRASH', 'nan', 567443,
       '2023-01-12 06:58:54.000',
       'Congratulations Team VIT - DESH Department for Receiving Best Paper Award',
       '[image: image.png]\r\n']
label_values = {'CHAT': 2,
            'TRASH': 8, 
            'SPAM': 7, 
            'CATEGORY_FORUMS': 4, 
            'CATEGORY_UPDATES':5, 
            'CATEGORY_PROMOTIONS':6, 
            'CATEGORY_SOCIAL':6, 
            'UNREAD': 4
            }
print(get_score(a,label_values) )