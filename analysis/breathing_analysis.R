install.packages("ggplot2")
install.packages("gplots")
install.packages("data.table")
install.packages("dplyr")

library(dplyr)
library(ggplot2)
library(gplots)
library(data.table)


## import breathing data
breathing <- read.csv("/Users/xinsui/Google Drive/interoception_project/analysis/breathing_responses.csv")

## check data 
head(breathing)

## subsetting the data
subset <- breathing[c("subject_id", "condition", "difficulty", "comfort")]
names(subset) <- c("id", "condition", "intense", "unpleasant")

## aggregate
mean_aggregate <- aggregate(.~id+condition, subset, mean)
sd_aggregate <- aggregate(.~id+condition, subset, sd)
median_aggregate <- aggregate(.~id+condition, subset, median)
max_aggregate <- aggregate(.~id+condition, subset, max)
min_aggregate <- aggregate(.~id+condition, subset, min)


# For Inner Join
multi_inner <- Reduce(
  function(x, y, ...) merge(x, y, ...), 
  flightsList
)

aggregate <- merge(merge(merge(merge(
  mean_aggregate, 
  sd_aggregate, by=c("id", "condition")),
  median_aggregate, by=c("id", "condition")),
  max_aggregate, by=c("id", "condition")),
  min_aggregate, by=c("id", "condition")
  )
          
names(aggregate) <- c("id", "condition",
                      "intense_mean", "unpleasant_mean", 
                      "intense_sd", "unpleasant_sd", 
                      "intense_median", "unpleasant_median",
                      "intense_max", "unpleasant_max",
                      "intense_min", "unpleasant_min"
                      )

## plots by condition by subject
#
ggplot(breathing[breathing$subject_id == "i213",], 
       aes(x=trial, y=difficulty)
) + 
  geom_line() + 
  geom_point()

# mean_intense with sd bar
ggplot(aggregate[aggregate$id == "i213",], 
       aes(x=condition, y=intense_mean)
       ) +  
  geom_errorbar(aes(ymin=intense_mean-intense_sd, ymax=intense_mean+intense_sd), width=.2) +
  geom_line() +
  geom_point()

# median_intense with min-max bar
ggplot(aggregate[aggregate$id == "i203",], 
       aes(x=condition, y=intense_median)
       ) + 
  geom_errorbar(aes(ymin=intense_min, ymax=intense_max), width=.2) +
  geom_line() +
  geom_point()

# mean_unpleasant with sd bar
ggplot(aggregate[aggregate$id == "i213",], 
       aes(x=condition, y=mean_unpleasant)
       ) + 
  geom_errorbar(aes(ymin=mean_unpleasant-sd_unpleasant, ymax=mean_unpleasant+sd_unpleasant), width=.2) + 
  geom_line() + 
  geom_point()

# median_unpleasant with min-max bar
ggplot(aggregate[aggregate$id == "i213",], 
       aes(x=condition, y=median_unpleasant)
) + 
  geom_errorbar(aes(ymin=min_unpleasant, ymax=max_unpleasant), width=.2) +
  geom_line() +
  geom_point()


## calculate the detection accuracy rates
aggregate_intense <- aggregate[,c("id", "condition", "intense_mean", "intense_sd", "intense_median", "intense_max", "intense_min")]

aggregate_intense_at0 <- aggregate_intense[aggregate$condition == 0,][-aggregate$condition]

aggregate_intense_at0 <- aggregate_intense_at0[-c(2)]

names(aggregate_intense_at0) <- c("id", "intense_mean_at0", "intense_sd_at0", "intense_median_at0", "intense_max_at0", "intense_min_at0")

detection_accuracy <- merge(subset[subset$condition > 0, ], aggregate_intense_at0, by="id", all=TRUE)


detection_accuracy$detected_byMean <- ifelse(detection_accuracy$intense > detection_accuracy$intense_mean_at0, 1, 0)

detection_accuracy$detected_byMedian <- ifelse(detection_accuracy$intense > detection_accuracy$intense_median_at0, 1, 0)


detection_accuracy_aggregate <- aggregate(.~id, detection_accuracy, sum)

detection_accuracy_rate <- detection_accuracy_aggregate[, c("id", "detected_byMean", "detected_byMedian")]


detection_accuracy_rate$accuracy_rate_byMean <- detection_accuracy_rate$detected_byMean/(30-30/5)

detection_accuracy_rate$accuracy_rate_byMedian <- detection_accuracy_rate$detected_byMedian/(30-30/5)

## scatter plots for correlation between intense and unpleasant by subject
subset$condition <- as.factor(subset$condition)
#subset$id <- as.factor(subset$id)

remove(sub_subset_bySubject)
sub_subset_bySubject <- subset[subset$id == "i211",]

ggplot(subset_bySubject, aes(x=subset_bySubject$intense, 
                             y=subset_bySubject$unpleasant,
                             shape=subset_bySubject$condition,
                             color=subset_bySubject$condition)
       ) +
  geom_point() +
  geom_text(label=subset_bySubject$condition) +
  xlim(0,10) + 
  ylim(0,10) +
  geom_abline(slope=1, intercept=0) +
  labs(title="Unpleasant vs. Intense",
       x="Intense (0-10)", 
       y = "Unpleasant/(0-10)") 



