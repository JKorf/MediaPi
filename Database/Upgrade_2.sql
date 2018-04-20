ALTER TABLE UnfinishedTorrents
  RENAME TO UnfinishedItems;

ALTER TABLE UnfinishedItems
  ADD Type TEXT;