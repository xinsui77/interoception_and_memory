install.packages("ggplot2")
install.packages("gplots")
install.packages("data.table")

library(ggplot2)
library(gplots)
library(data.table)


## import heartbeat_responses.csv data
heartbeat <- read.csv("/Users/xinsui/Google Drive/000 Intereoception_project/Analysis/heartbeat_responses_R.csv")

head(heartbeat)
tail(heartbeat)

## create columns for binary values representing [hit, miss, false alarm, and correct_rejection]
heartbeat$hit <- ifelse(heartbeat$condition == 0 & heartbeat$response == 0, 1, 0)
heartbeat$miss <- ifelse(heartbeat$condition == 0 & heartbeat$response == 1, 1, 0)
heartbeat$falseAlarm <- ifelse(heartbeat$condition == 1 & heartbeat$response == 0, 1, 0)
heartbeat$correctRejection <- ifelse(heartbeat$condition == 1 & heartbeat$response == 1, 1, 0)

head(heartbeat)
tail(heartbeat)

## total sum across all subjects of [hit, miss, false alarm, and correct_rejection]
group_sum_hit <- sum(heartbeat$hit)
group_sum_miss <- sum(heartbeat$miss)
group_sum_falseAlarm <- sum(heartbeat$falseAlarm)
group_sum_correctRejection <- sum(heartbeat$correctRejection)
group_sums <- cbind(group_sum_hit, group_sum_miss, group_sum_falseAlarm, group_sum_correctRejection)
group_sums


## sum within each subjects of [hit, miss, false alarm, and correct_rejection]
individual_sums <- aggregate(cbind(heartbeat$hit, heartbeat$miss, heartbeat$falseAlarm, heartbeat$correctRejection), by=list(id=heartbeat$id), FUN=sum)
individual_sums

names(individual_sums) <- c("id", "hit", "miss", "falseAlarm", "correctRejection")

individual_sums$hit_rate <- individual_sums$hit/25
individual_sums$falseAlarm_rate <- individual_sums$falseAlarm/25

individual_sums

## functions for calculating A and b
A <-function(h,f)
{
  if(f<=.5 & h>=.5)
  {
    a <- .75 + (h-f)/4 - f*(1-h)
  } else if(f<=h & h<=.5)
  {
    a <- .75 + (h-f)/4 - f/(4*h)
  } else {
    a <- .75 + (h-f)/4 - (1-h)/(4 * (1-f))
  }
  return(a)
}

b <- function(h,f)
{
  if(f<=.5 & h>=.5)
  {
    b <-(5-4*h)/(1+4*f)
  } else if(f<=h & h<=.5)
  {
    b <-(h^2+h)/(h^2+f)
  } else {
    b <- ((1-f)^2 + (1-h))/((1-f)^2 + (1-f))
  }
  return(b)
}

## 
A_estimate <- A(individual_sums$hit_rate, individual_sums$falseAlarm_rate)
