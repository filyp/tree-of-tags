- On LessWrong, for some reason the cluster of democratic posts is clearly separated from meritocratic posts
- There are no redundant tags - only 13 pairs of EA forum tags have >50% overlap.
- Democratic and meritocratic scores have 93% correlation!
- Only 6% of all pairs of tags cooccur with each other.
- 16%! of posts on AF have no score
- there are 1k tags, 10k posts, and 100k comments on EA forum
- 96% of posts have both democratic and meritocratic scores positive

- Any 'alpha' clustering parameter above 1.1 looks fine - this means alpha choice is not important - let's just assume a safe value of 1.5.

- TODO? ask someone? - category tags (those displayed in white, at the end of the list of tags) aren't listed by GraphQL `tags` query, but are listed by the posts. It seems the server has some information that it doesn't expose through GraphQL.
- I can't get PostAnalytics query to work, but it would be nice to have this info.