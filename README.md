Databases


  create table game
  (
      id           int auto_increment
          primary key,
      money        int(8)      null,
      location     varchar(10) null,
      screen_name  varchar(40) null,
      player_range int         null
  )
   charset = latin1;
