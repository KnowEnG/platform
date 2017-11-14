#                    University of Illinois/NCSA
#                        Open Source License
# 
#         Copyright(C) 2014-2015, The Board of Trustees of the
#             University of Illinois.  All rights reserved.
# 
#                           Developed by:
# 
#                          Visual Analytics
#                    Applied Research Institute
#             University of Illinois at Urbana-Champaign
# 
#                http://appliedresearch.illinois.edu/
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal with the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# + Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimers.
# + Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimers in
#   the documentation and/or other materials provided with the distribution.
# + Neither the names of The PerfSuite Project, NCSA/University of Illinois
#   at Urbana-Champaign, nor the names of its contributors may be used to
#   endorse or promote products derived from this Software without specific
#   prior written permission.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS WITH THE SOFTWARE.


library("ggplot2")
library("gplots")
library("grid")
library("MASS")
library("plyr")
library("reshape2")
library("scales")

save.plot <- function(plot.title,save.type="pdf",h=12,w=12){
  # Directs all subsequent plot commands to be saved
  # Note: should be proceeded by dev.off()
  #
  # Args:
  #  plot.title: The name by which the plot file will be saved
  #  save.type: the document type to be saved as
  #  h,w: height and width of plot to be saved as in inches
  #
  # Returns:
  #  nothing
  plot.title <- gsub(" ", "_", plot.title)
  if(save.type=="jpeg")
  {
    jpeg(paste(plot.title,".jpeg",sep=""),width=w*100,height=h*100)
  }
  if(save.type=="pdf")
  {
    pdf(paste(plot.title,".pdf",sep=""),width=w,height=h)
  }
  else if(save.type=="eps")
  {
    setEPS()
    postscript(paste(plot.title,".eps",sep=""),height=h,width=w)
  }
}

plot.parameter.search.stats <- function(df.stats){
  # Plots stats from REFUSE's parameter_search.
  #
  # Args:
  #  df.stats: Data frame containing the statistical measures to plot.
  #
  # Returns:
  #  nothing
  pdf("Parameter_Search-Moments.pdf",width=12,height=8)
  par(mfrow=c(4,2))
  plot(df.stats$ntree,df.stats$mean,type="l",main="Mean")
  plot(df.stats$ntree,df.stats$median,type="l",main="Median")
  plot(df.stats$ntree,df.stats$mode,type="l",main="Mode")
  plot(df.stats$ntree,df.stats$var,type="l",main="Variance")
  plot(df.stats$ntree,df.stats$skewness,type="l",main="Skewness")
  plot(df.stats$ntree,df.stats$kurtosis,type="l",main="Pearson's Kurtosis")
  plot(df.stats$ntree,df.stats$ks_p,type="l",main="Kolmogorov-Smirnov P.Value")
  plot(df.stats$ntree,df.stats$corr,type="l",main="Correlation")
  dev.off()
}

plot.parameter.search.growth <- function(df.growth.storage){
  # Plots reps from REFUSE's parameter_search.
  #
  # Args:
  #  df.growth.storage: Data frame containing the RF results for each rep.
  #
  # Returns:
  #  nothing
  pdf("Parameter_Search.pdf",width=12,height=8)
  parcoord(df.growth.storage, col=rainbow(length(df.growth.storage[,1])), var.label=TRUE)
  dev.off()
}

plot.compare.methods <- function(data.results){
  pdf("Correlation_Comparison_1.pdf",height=8,width=12)
  parcoord(data.results[, c("mean", "var", "vim", "pearson", "kendall", "spearman")], col=factor(data.results$segment3), var.label=TRUE)
  dev.off()

  # Dot Plot
  plot.importance(data.results$vim,data.results$name,data.results$group,"All Features S curve")
}

plot.importance <-function(vim,labels,group,main,palette=NULL,label=F)
{ 
  # Produces a Dot plot of Features based upon Variable Importance Metrics
  # 
  # Args:
  #  vim: vector of numerics denoting the Variable Importance Metric value
  #  labels: vector of characters that names the Feature ascocited with each vim
  #  group: vector of characters that will be used for color coding a feature
  #  main: character string that will be used during the naming of the plot
  #  palette: vector of colors that will be used for color coding a feature
  #  label: boolean control over label usage in plot 
  #
  # Returns: nothing
  
  # Begin Plotting
  plt <-qplot(vim,
              1:length(vim),
              colour=group,
              #labels=labels,
              xlim=c(min(vim),max(vim)*1.05),#Multiplier controls how much buffer space there is on the right side of plot
              xlab="Feature Importance Metric \n<<< Less Significant | More Significant >>>",
              ylab="Feature Importance Ranking",
              main=paste("Variable Importance Ranking"))
  # Optional Labeling for Points
  if(label==T)
  {
    plt <- plt + geom_text(aes(x=vim*1.005,
                               y=1:length(vim)),
                               #label=labels),
                           size=3,
                           hjust=0,
                           vjust=0.5)
  }

  # Color Coding of Plot
  if(is.null(palette))
  {
    palette <- c("#d66166", "#fdb800", "#ff8f57", "#81b578", "#c4acfc", "#96e0d7", "#D55E00", "#CC79A7","#000000")
    if(length(palette) < nlevels(factor(group)))
    {
      palette <- rainbow(nlevels(factor(group)))
    } else {
      palette <- head(palette,nlevels(factor(group)))
    }
  }
  plt <- plt + scale_fill_manual(values=palette)
  plt <- plt + scale_colour_manual(values=palette)
  
  # Save plot object
  save.plot(main)
  print(plt)
  dev.off() 
}

plot.summary.vis <- function(df_x_best, s_y){
  # Visualize feature space for classification repsonse through a series of plots
  #
  # Args:
  #  df_x_best: feature columns and sample rows (n,p) for best predictors
  #  s_y: response factor vector (must be classification)
  #
  # Returns:
  #  just saves plots to a folder
  
  # Scale 0-1 
  for(i in 1:ncol(df_x_best))
  {
    # Assign colspace i to x as a double vector
    x <- as.double(as.character(df_x_best[[i]]))
    x <- (x-min(x))/(max(x)-min(x))
    df_x_best[i]<-x
  }
  
  # Map colors to a vector for plotting red vs blue
  color.map <- function(val) { if (val==1) "#FF0000" else "#0000FF" }
  example.colors <- unlist(lapply(as.list(as.numeric(factor(s_y))), color.map))

  # Classical L2 norm Metric Dimensional Scaling
  pdf("CMDS.pdf",width=12,height=12)
  d <- dist(df_x_best) # euclidean distances between the rows
  fit <- cmdscale(d,eig=TRUE, k=2) # k is the number of dim
  dim1 <- fit$points[,1]
  dim2 <- fit$points[,2]
  plot(dim1, dim2, xlab="Coordinate 1", ylab="Coordinate 2",
       main="Clasical L2 Metric MDS",type="n")
  text(dim1, dim2, labels = row.names(df_x_best), cex=1.5,col=example.colors) 
  dev.off()
  
  # Non-Metric L2 Dimensioanl scaling plot
# REMOVING UNTIL BUG TOOL-32 IS FIXED
#  pdf("NMDS.pdf",width=12,height=12)
#  d <- dist(df_x_best) # euclidean distances between the rows
#  fit <- isoMDS(d, k=2) # k is the number of dim
#  dim1 <- fit$points[,1]
#  dim2 <- fit$points[,2]
#  plot(dim1, dim2, xlab="Coordinate 1", ylab="Coordinate 2",
#       main="Non-Metric L2 MDS",type="n")
#  text(dim1, dim2, labels = row.names(df_x_best), cex=1.5,col=example.colors)
#  dev.off()
  
  # PCA plot with Feature Projections
# REMOVING UNTIL BUG TOOL-33 IS FIXED
#  pdf("Biplot.pdf",width=12,height=8)
#  data.pca <- prcomp(df_x_best)
#  plt <- ggbiplot2(pcobj = data.pca,groups=factor(s_y),cex=2,choices=c(1,2),circle=TRUE,ellipse=TRUE,labels=row.names(df_x_best))
#  print(plt)
#  dev.off()
  
  # LDA projection plot
  tryCatch(
    {
      pdf("LDA_Index.pdf",width=12,height=12)
      data.lda <- lda(df_x_best,grouping=factor(s_y),method="moment")
      data.lda <- predict(data.lda)
      ldd <- data.lda$x[,1]
      plot(ldd,col=example.colors,cex=3)
      dev.off()
      
      # LDA KDE Projection plot
      pdf("LDA_Distribution.pdf")
      plt <- ggplot(data.frame(ldd,s_y),aes(ldd,fill=factor(s_y),col=factor(s_y))) + geom_density(alpha=.5) + geom_rug(alpha=.75)
      cbPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#0072B2", "#a885ff", "#D55E00", "#CC79A7","#000000")
      if (length(cbPalette) < nlevels(factor(s_y)))
      {
        cbPalette <- rainbow(nlevels(factor(s_y)))
      }
      plt <- plt + scale_fill_manual(values=head(cbPalette,nlevels(factor(s_y))))
      plt <- plt + scale_colour_manual(values=head(cbPalette,nlevels(factor(s_y))))
      plt <- plt + xlab("Linear Discriminant Projection Dimension") + ylab("Count")
      print(plt)
      dev.off()
    },
    error=function(cond) {
      print(paste("WARNING: ", cond))
    },
    warning=function(cond) {
      print(paste("WARNING: ", cond))
    },
    finally={
      dev.off(2)
    }
  )
  
  # HeatMap
# REMOVING UNTIL BUG TOOL-33 IS FIXED
#  pdf("HeatMap.pdf",
#      width=20,
#      height=15)
#  
#  heatmap.2(t(as.matrix(df_x_best)),
#            main="Heat Map",
#            xlab="Samples N",
#            ylab="Features P",
#            col=topo.colors(75), 
#            scale="none", 
#            ColSideColors=example.colors,
#            key=TRUE, 
#            symkey=FALSE,
#            density.info="histogram",
#            trace="none", 
#            cexRow=2,
#            cexCol=2,
#            mar=c(8,45))
#  
#  dev.off()
}

# This was pasted from a code repository
# I forget where but we could find it if needed
ggbiplot2 <- function(pcobj, choices = 1:2, scale = 1, pc.biplot = TRUE, 
                      obs.scale = 1 - scale, var.scale = scale, 
                      groups = NULL, ellipse = FALSE, ellipse.prob = 0.68, 
                      labels = NULL, labels.size = 3, alpha = 1, 
                      var.axes = TRUE, 
                      circle = FALSE, circle.prob = 0.69, 
                      varname.size = 3, varname.adjust = 1.5, 
                      varname.abbrev = FALSE, ...)
{
  
  stopifnot(length(choices) == 2)
  
  if(inherits(pcobj, 'prcomp')){
    nobs.factor <- sqrt(nrow(pcobj$x) - 1)
    d <- pcobj$sdev
    u <- sweep(pcobj$x, 2, 1 / (d * nobs.factor), FUN = '*')
    v <- pcobj$rotation
  } else if(inherits(pcobj, 'princomp')) {
    nobs.factor <- sqrt(pcobj$n.obs)
    d <- pcobj$sdev
    u <- sweep(pcobj$scores, 2, 1 / (d * nobs.factor), FUN = '*')
    v <- pcobj$loadings
  } else if(inherits(pcobj, 'PCA')) {
    nobs.factor <- sqrt(nrow(pcobj$call$X))
    d <- unlist(sqrt(pcobj$eig)[1])
    u <- sweep(pcobj$ind$coord, 2, 1 / (d * nobs.factor), FUN = '*')
    v <- sweep(pcobj$var$coord,2,sqrt(pcobj$eig[1:ncol(pcobj$var$coord),1]),FUN="/")
  } else {
    stop('Expected a object of class prcomp, princomp or PCA')
  }
  
# BUG TOOL-33: fails here with u[,choices] subscript out of bounds
  # Scores
  df.u <- as.data.frame(sweep(u[,choices], 2, d[choices]^obs.scale, FUN='*'))
  
  # Directions
  v <- sweep(v, 2, d^var.scale, FUN='*')
  df.v <- as.data.frame(v[, choices])
  
  names(df.u) <- c('xvar', 'yvar')
  names(df.v) <- names(df.u)
  
  if(pc.biplot) {
    df.u <- df.u * nobs.factor
  }
  
  # Scale the radius of the correlation circle so that it corresponds to 
  # a data ellipse for the standardized PC scores
  r <- 1
  
  # Scale directions
  v.scale <- rowSums(v^2)
  df.v <- df.v / sqrt(max(v.scale))
  
  ## Scale Scores
  r.scale=sqrt(max(df.u[,1]^2+df.u[,2]^2))
  df.u=.99*df.u/r.scale
  
  # Change the labels for the axes
  if(obs.scale == 0) {
    u.axis.labs <- paste('standardized PC', choices, sep='')
  } else {
    u.axis.labs <- paste('PC', choices, sep='')
  }
  
  # Append the proportion of explained variance to the axis labels
  u.axis.labs <- paste(u.axis.labs, 
                       sprintf('(%0.1f%% explained var.)', 
                               100 * pcobj$sdev[choices]^2/sum(pcobj$sdev^2)))
  
  # Score Labels
  if(!is.null(labels)) {
    df.u$labels <- labels
  }
  
  # Grouping variable
  if(!is.null(groups)) {
    df.u$groups <- groups
  }
  
  # Variable Names
  if(varname.abbrev) {
    df.v$varname <- abbreviate(rownames(v))
  } else {
    df.v$varname <- rownames(v)
  }
  
  # Variables for text label placement
  df.v$angle <- with(df.v, (180/pi) * atan(yvar / xvar))
  df.v$hjust = with(df.v, (1 - varname.adjust * sign(xvar)) / 2)
  
  # Base plot
  g <- ggplot(data = df.u, aes(x = xvar, y = yvar)) + 
    xlab(u.axis.labs[1]) + ylab(u.axis.labs[2]) + coord_equal()
  
  if(var.axes) {
    # Draw circle
    if(circle) 
    {
      theta <- c(seq(-pi, pi, length = 50), seq(pi, -pi, length = 50))
      circle <- data.frame(xvar = r * cos(theta), yvar = r * sin(theta))
      g <- g + geom_path(data = circle, color = muted('white'), 
                         size = 1/2, alpha = 1/3)
    }
    
    # Draw directions
    g <- g +
      geom_segment(data = df.v,
                   aes(x = 0, y = 0, xend = xvar, yend = yvar),
                   arrow = arrow(length = unit(1/2, 'picas')), 
                   
                   color = muted('red'))
  }
  
  # Draw either labels or points
  if(!is.null(df.u$labels)) {
    if(!is.null(df.u$groups)) {
      g <- g + geom_text(aes(label = labels, color = groups), 
                         size = labels.size)
    } else {
      g <- g + geom_text(aes(label = labels), size = labels.size)      
    }
  } else {
    if(!is.null(df.u$groups)) {
      g <- g + geom_point(aes(color = groups), alpha = alpha)
    } else {
      g <- g + geom_point(alpha = alpha)      
    }
  }
  
  # Overlay a concentration ellipse if there are groups
  if(!is.null(df.u$groups) && ellipse) {
    theta <- c(seq(-pi, pi, length = 50), seq(pi, -pi, length = 50))
    circle <- cbind(cos(theta), sin(theta))
    
    ell <- ddply(df.u, 'groups', function(x) {
      if(nrow(x) < 2) {
        return(NULL)
      } else if(nrow(x) == 2) {
        sigma <- var(cbind(x$xvar, x$yvar))
      } else {
        sigma <- diag(c(var(x$xvar), var(x$yvar)))
      }
      mu <- c(mean(x$xvar), mean(x$yvar))
      ed <- sqrt(qchisq(ellipse.prob, df = 2))
      data.frame(sweep(circle %*% chol(sigma) * ed, 2, mu, FUN = '+'), 
                 groups = x$groups[1])
    })
    names(ell)[1:2] <- c('xvar', 'yvar')
    g <- g + geom_path(data = ell, aes(color = groups, group = groups))
  }
  
  # Label the variable axes
  if(var.axes) {
    g <- g + 
      geom_text(data = df.v, 
                aes(label = varname, x = xvar, y = yvar, 
                    angle = angle, hjust = hjust), 
                color = 'darkred', size = varname.size)
  }
  # Change the name of the legend for groups
  # if(!is.null(groups)) {
  #   g <- g + scale_color_brewer(name = deparse(substitute(groups)), 
  #                               palette = 'Dark2')
  # }
  
  # TODO: Add a second set of axes
  
  return(g)
}

plot.stability <- function(importance,stability,labels,factor.colour,palette,main,label=F,
                           xlabel="Feature Importance Metric (mean) \n<<< Less Significant | More Significant >>>",
                           ylabel="Sensitivity (var) \n<<< Less Sensitive | More Sensitive >>>",
                           info="No Info Passed")
{
  # Begin Plotting
  plt <-qplot(importance,
              stability,
              colour=factor.colour,
              #shape=factor.shape,
              #labels=labels,
              size=10,
              xlim=c(min(importance),max(importance)*1),#Multiplier controls how much buffer space there is on the right side of plot
              xlab=xlabel,
              ylab=ylabel,
              main=main)
  
  # Optional Labeling for Points
  if(label==T)
  {
    plt <- plt + geom_text(aes(x=max(importance)*1.05,
                               y=stability),
                               #label=labels),
                           size=3,
                           hjust=0,
                           vjust=0.5)
  }
  
  plt <- plt + annotation_custom(
    grob = textGrob(label = info, hjust = 0,vjust = 0, gp = gpar(cex = 1)),
    ymin = min(stability),      # Vertical position of the textGrob
    ymax = min(stability),
    xmin = max(importance)*1.07,# Note: The grobs are positioned outside the plot area
    xmax = max(importance)*1.07)
  
  # Color Coding of Plot
  plt <- plt + scale_fill_manual(values=palette)
  plt <- plt + scale_colour_manual(values=palette)
  
  # Save plot object
  save.plot(main)
  # Code to override clipping
  gt <- ggplot_gtable(ggplot_build(plt))
  gt$layout$clip[gt$layout$name == "panel"] <- "off"
  grid.draw(gt)
  dev.off() 
}

plot.importance.box <-function(df.vim.reps,df.supplement,palette,title,type="box",add.labels=T,info="No information passed")
{ 
  # Produces a box plot of Features based upon Variable Importance Metrics
  # 
  # Args:
  #  df.vim.reps: dataframe produced by prep.importance function
  #  df.supplement: dataframe of features, p_vals, and groups, sorted by descending p_val
  #  palette: vector of colors for color-coding by group
  #  title: title of plot
  #  type: string identifier for the type of box plot
  #  add.label: boolean control over label usage in plot
  #  info: string providing additional info to be included on plot 
  #
  # Returns: nothing

  # -- 
  # need dataframe with one row per feature per refuse rep
  # columns are feature names, feature groups, and vim values
  # rows ordered by mean vim
  # --

  # first, sort the features according to mean vim
  mean.vims <- sort(colMeans(df.vim.reps), decreasing=FALSE)

  # now melt df.vim.reps into a tall df ordered by mean.vims
  df.melted <- melt(df.vim.reps, na.rm=FALSE, measure.vars=names(mean.vims))
  colnames(df.melted) <- c("Feature.Name", "VIM")

  # join groups
  df.groups <- data.frame("Feature.Name"=make.names(rownames(df.supplement)), "Feature.Source"=df.supplement$group)
  df.melted <- join(df.melted, df.groups, by="Feature.Name")

  # -- df.melted is now the dataframe we needed

  # need dataframe with feature names, max vims, global max vim, global min vim, p_vals, and groups
  # ordered to match mean.vims
  # df.label is that dataframe
  max.vims <- apply(df.vim.reps, MARGIN=c(2), max)
  df.p.vals <- data.frame("Feature.Name"=make.names(rownames(df.supplement)), "p.val"=paste(round(df.supplement$p_val*100, digits=3), c("%"), sep=""))
  df.label <- data.frame("Feature.Name"=names(mean.vims), "max.vim"=max.vims[names(mean.vims)])
  df.label$right <- rep(max(df.label$max.vim), length(df.label[[1]]))
  df.label$left <- rep(min(df.melted$VIM), length(df.label[[1]]))
  df.label <- join(df.label, df.groups, by="Feature.Name")
  df.label <- join(df.label, df.p.vals, by="Feature.Name")

  # Establish ggplot2 object
  plt <- ggplot(df.melted,aes(Feature.Name,VIM))
  # Default Labeling
  plt <- plt + xlab("Features") + ylab("Variable Importance Metric\n <<< Less Significant | More Significant >>>")
  # Colours
  plt <- plt + scale_fill_manual(values=palette)
  plt <- plt + scale_colour_manual(values=palette)
  plt <- plt + ggtitle(title)+theme(axis.text.y = element_blank())#theme(plot.title = element_text(lineheight=.8, face="bold"))
  
  # Boxes or Violins
  if(type=="box"){plt <- plt + geom_boxplot(aes(fill = Feature.Source,colour=Feature.Source),outlier.colour="#b5b5b5",outlier.size=1.5,) + coord_flip()}
  else if(type=="violin"){plt <- plt + geom_violin(aes(fill = Feature.Source)) + coord_flip()}
  gt <- ggplot_gtable(ggplot_build(plt))
  gt$layout$clip[gt$layout$name == "panel"] <- "off"
  
  save.plot(title,h=12,w=22)
  grid.draw(gt)
  dev.off()
  
  # Theme Customization
  plt <- plt + theme(plot.title = element_text(face="bold", colour="#000000", size=15),
                     legend.position = "top",
                     axis.title.y = element_text(face="bold", colour="#000000", size=10),
                     axis.title.x = element_text(face="bold", colour="#000000", size=10),
                     panel.background = element_rect(fill="NA",colour="NA"),                     
                     plot.background = element_rect(colour="NA"),
                     #panel.grid.major = element_line(colour = "NA"),
                     #panel.grid.minor = element_line(colour = "NA"),
                     plot.margin = unit(c(1,20,.5,.5),"cm"))
  
  # Annotate plot with information
  plt <- plt + annotation_custom(
    grob = textGrob(label = info, hjust = 0,vjust = 0, gp = gpar(cex = .75)),
    ymin = max(df.label[[2]]),      # Vertical position of the textGrob
    ymax = max(df.label[[2]]),
    xmin = length(df.label[[2]])+2,# Note: The grobs are positioned outside the plot area
    xmax = length(df.label[[2]])+2)
  
  plt <- plt + annotation_custom(
    grob = textGrob(label = paste("Likelihood of\nrelevance"), hjust = 1,vjust = 0, gp = gpar(cex = 1)),
    ymin = min(df.melted$VIM),      # Vertical position of the textGrob
    ymax = min(df.melted$VIM),
    xmin = length(df.label[[2]])+1,# Note: The grobs are positioned outside the plot area
    xmax = length(df.label[[2]])+1)

  # Feature Name placed on the Right Side Margin
  plt <- plt + geom_text(aes(x=Feature.Name,
                             y=right*1.05,
                             label=paste("-------",Feature.Name),
                             colour=Feature.Source),
                         data=df.label,
                         size=4,
                         #family="Helvetica-Narrow",#"AvantGarde", "Bookman", "Courier", "Helvetica", "Helvetica-Narrow", "NewCenturySchoolbook", "Palatino" or "Times"
                         hjust=0,
                         vjust=0.5)
 
  # Feature P.Value
  plt <- plt + geom_text(aes(x=Feature.Name,
                             y=(left - abs(left*.05)),
                             label=p.val,
                             colour=Feature.Source),
                         data=df.label,
                         size=3,
                         hjust=1,
                         vjust=0.5)
  
  # Turn Clipping off
  gt <- ggplot_gtable(ggplot_build(plt))
  gt$layout$clip[gt$layout$name == "panel"] <- "off"
  
  # This plot should be made wide
  save.plot(title,h=12,w=22)
  grid.draw(gt)
  dev.off()
}

small.multiples <- function(x,y,vim,p,threshold=.5,a=3,b=4)
{
  # Produce and save samll multiples plots of features 
  #
  # Args:
  #  x: data frame with feature columns and sample rows (n,p)
  #  y: response vector of factors (not suitable for regression 12/4/2014)
  #  a: number of features to be included as rows per page
  #  b: number of features to be included as columns per page 
  #
  # Returns:
  #  Nothing
  
  page.num <- a*b
  count <- 1
  i <- 1
  
  # Outermost loop
  for(j in 1:min(ceiling(ncol(x)/page.num),3))# j indexes the number of plot sheets to be made. each plot sheet is axb
  {
    save.plot(paste("Small Multiples",j),h=a*2,w=b*2)
    plot.list=list()#(rep(ggplot(),a*b))# initialize emptylist
    counter <- 0
    while(counter < page.num && i <= ncol(x))# while the number of plots is less than axb and i < #of features
    {
      counter <- counter + 1
      cat(paste(counter,","))
      feature.name <- colnames(x)[i]
      feature.data <- x[[feature.name]]
       
      #ggplot density plot
      plt <- ggplot(data.frame(feature.data,y),aes(feature.data,fill=factor(y),col=factor(y))) + geom_density(adjust=2,alpha=.5,) + geom_rug(alpha=.5)
      cbPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#0072B2", "#a885ff", "#D55E00", "#CC79A7","#000000")
      if(length(cbPalette) < nlevels(factor(y)))
      {
        cbPalette <- rainbow(nlevels(factor(y)))
      }
      plt <- plt + scale_fill_manual(values=head(cbPalette,nlevels(factor(y))))
      plt <- plt + scale_colour_manual(values=head(cbPalette,nlevels(factor(y))))
      if(i > 1){plt <- plt + theme(legend.position="none")}    
      plt <- plt + xlab(feature.name) + ylab("Probability Density")
      
      # Add grob to list don't forget that grob is a list
      plot.list[[length(plot.list)+1]] <- plt # the double brackets are critical
      i <- i + 1
    }
    print(plot.list)
    args.list <- c(plot.list,list(nrow=a,ncol=b))
    # do.call(grid.arrange,args.list)
    dev.off()
  }
}
