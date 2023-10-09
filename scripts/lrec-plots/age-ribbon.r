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
    ylim(30, 70) +
    labs(y = "age distribution") +
    theme(
        panel.background = element_rect(fill = 'white',
                                        colour = 'gray',
                                        linetype = 1
                                        ),
        panel.grid.major = element_line(size = 0.5,
                                        colour = "grey90",
                                        linetype = 3
                                        ),
        text = element_text(size=16),
        #axis.text.x = element_blank()
        axis.title.x = element_blank()
    )


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
