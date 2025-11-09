# I have a date in this format todaydate = '2023-05-16' this is a string
# and I want to create a string that goes from date May 16 to December 30 in year 2023
# I will iterate the string per month

todaydate = '2023-05-17'

todayyear = todaydate[:4]
todaymonth = todaydate[5:7]
todayday = todaydate[8:10]

print("strYear = ", todayyear)
print("strMonth = ", todaymonth)
print("strDay = ", todayday)

# another crappy way
# define arrar with the dates hardcoded
# define an array with all the dates to use
datestouse = ['2023-05-17', '2023-05-18', '2023-05-19', '2023-05-20', '2023-05-21', '2023-05-22', '2023-05-23', '2023-05-24', '2023-05-25', '2023-05-26', '2023-05-27', '2023-05-28', '2023-05-29', '2023-05-30', '2023-05-31']

# iterate on the array
for todaydate in datestouse:
    print(todaydate)