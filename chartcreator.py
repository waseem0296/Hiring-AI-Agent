import matplotlib.pyplot as plt

# Data from Table 2: Risk Distribution by Category
categories = ['Technical', 'Managerial', 'Organizational', 'External']
percentages = [35.7, 28.6, 21.4, 14.3]

# Different colors for each category
colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']

# Create pie chart
plt.figure()
plt.pie(
    percentages,
    labels=categories,
    autopct='%1.1f%%',
    startangle=140,
    colors=colors
)

# Title
plt.title('Risk Distribution by Category')

# Equal aspect ratio ensures the pie is circular
plt.axis('equal')

# Display the chart
plt.show()
