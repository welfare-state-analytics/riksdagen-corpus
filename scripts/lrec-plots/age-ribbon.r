#!/usr/bin/env Rscript

#install.packages("dplyr")
library("ggplot2")
library("dplyr")

ages <- read.csv("_age_df.csv", sep=';')
summary(ages)
head(ages)

ages2 <- ages %>%
    group_by(year) %>%
    summarize(
        n_cases = n(),
        mina = min(age),
        #ffq =  quantile(age, .10),
        fquant = quantile(age, .25),
        mean = mean(age),
        tquant = quantile(age, .75),
        #ttq = quantile(age, .90),
        maxa = max(age)
    )
head(ages2)

p <- ages2 %>% ggplot(aes(x=year)) +
    #geom_ribbon(aes(ymin=ffq, ymax=ttq), fill='grey80') +
    geom_ribbon(aes(ymin=fquant, ymax=tquant), fill='grey60') +
    geom_line(aes(y=mean)) +
    ylim(15, 80) +
    labs(y = "age distribution")


ggsave(
  "_age-ribbon.pdf",
  plot = p,
  scale = 1,
  width = 150,
  height = 150,
  units = "mm",
  dpi = 300,
  bg = NULL,
)
