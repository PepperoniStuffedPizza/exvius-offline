.class public final Lcom/exvius/local/UpdatePrompt;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.implements Landroid/content/DialogInterface$OnClickListener;
.implements Landroid/content/DialogInterface$OnCancelListener;

.field private final activity:Landroid/app/Activity;
.field private final message:Ljava/lang/String;
.field public final latch:Ljava/util/concurrent/CountDownLatch;
.field public volatile answer:I

.method private constructor <init>(Landroid/app/Activity;Ljava/lang/String;)V
    .locals 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/exvius/local/UpdatePrompt;->activity:Landroid/app/Activity;
    iput-object p2, p0, Lcom/exvius/local/UpdatePrompt;->message:Ljava/lang/String;
    new-instance v0, Ljava/util/concurrent/CountDownLatch;
    const/4 v1, 0x1
    invoke-direct {v0, v1}, Ljava/util/concurrent/CountDownLatch;-><init>(I)V
    iput-object v0, p0, Lcom/exvius/local/UpdatePrompt;->latch:Ljava/util/concurrent/CountDownLatch;
    const/4 v1, -0x3
    iput v1, p0, Lcom/exvius/local/UpdatePrompt;->answer:I
    return-void
.end method

.method public run()V
    .locals 3
    :try_start_0
    new-instance v0, Landroid/app/AlertDialog$Builder;
    iget-object v1, p0, Lcom/exvius/local/UpdatePrompt;->activity:Landroid/app/Activity;
    invoke-direct {v0, v1}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v1, "Game data update available"
    invoke-virtual {v0, v1}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    iget-object v1, p0, Lcom/exvius/local/UpdatePrompt;->message:Ljava/lang/String;
    invoke-virtual {v0, v1}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const-string v1, "Download"
    invoke-virtual {v0, v1, p0}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v1, "Not now"
    invoke-virtual {v0, v1, p0}, Landroid/app/AlertDialog$Builder;->setNeutralButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v1, "Skip this update"
    invoke-virtual {v0, v1, p0}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v0, p0}, Landroid/app/AlertDialog$Builder;->setOnCancelListener(Landroid/content/DialogInterface$OnCancelListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v0}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0
    return-void
    :catch_0
    move-exception v0
    iget-object v1, p0, Lcom/exvius/local/UpdatePrompt;->latch:Ljava/util/concurrent/CountDownLatch;
    invoke-virtual {v1}, Ljava/util/concurrent/CountDownLatch;->countDown()V
    return-void
.end method

.method public onClick(Landroid/content/DialogInterface;I)V
    .locals 1
    iput p2, p0, Lcom/exvius/local/UpdatePrompt;->answer:I
    iget-object v0, p0, Lcom/exvius/local/UpdatePrompt;->latch:Ljava/util/concurrent/CountDownLatch;
    invoke-virtual {v0}, Ljava/util/concurrent/CountDownLatch;->countDown()V
    return-void
.end method

.method public onCancel(Landroid/content/DialogInterface;)V
    .locals 1
    const/4 v0, -0x3
    iput v0, p0, Lcom/exvius/local/UpdatePrompt;->answer:I
    iget-object v0, p0, Lcom/exvius/local/UpdatePrompt;->latch:Ljava/util/concurrent/CountDownLatch;
    invoke-virtual {v0}, Ljava/util/concurrent/CountDownLatch;->countDown()V
    return-void
.end method

# Called on the update worker thread when newer game data exists. Returns true to download it.
.method public static allowData(Landroid/content/Context;Lorg/json/JSONObject;)Z
    .locals 10
    const-string v0, "revision"
    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->getLong(Ljava/lang/String;)J
    move-result-wide v0
    const-string v2, "exvius_update_prompt"
    const/4 v3, 0x0
    invoke-virtual {p0, v2, v3}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v2
    const-string v3, "skip_data"
    const-wide/16 v4, -0x1
    invoke-interface {v2, v3, v4, v5}, Landroid/content/SharedPreferences;->getLong(Ljava/lang/String;J)J
    move-result-wide v4
    cmp-long v6, v4, v0
    if-nez v6, :cond_ask
    const/4 v6, 0x0
    return v6

    :cond_ask
    # wait up to 60 s for a visible screen to show the question on
    const/4 v6, 0x0
    :loop
    invoke-static {}, Lcom/exvius/local/DataUpdates;->access$200()Ljava/lang/ref/WeakReference;
    move-result-object v7
    invoke-virtual {v7}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;
    move-result-object v7
    check-cast v7, Landroid/app/Activity;
    if-eqz v7, :cond_wait
    invoke-virtual {v7}, Landroid/app/Activity;->isFinishing()Z
    move-result v8
    if-eqz v8, :cond_show
    :cond_wait
    const/16 v8, 0x3c
    if-lt v6, v8, :cond_sleep
    const/4 v8, 0x0
    return v8
    :cond_sleep
    const-wide/16 v8, 0x3e8
    invoke-static {v8, v9}, Ljava/lang/Thread;->sleep(J)V
    add-int/lit8 v6, v6, 0x1
    goto :loop

    :cond_show
    new-instance v8, Ljava/lang/StringBuilder;
    invoke-direct {v8}, Ljava/lang/StringBuilder;-><init>()V
    const-string v9, "Elvlin released new game data (revision "
    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v8, v0, v1}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;
    const-string v9, ").\n\nDownload it? It is applied the next time you fully close and reopen the game. Your save, Lapis Chest and 50,000 Lapis daily quests are kept.\n\nIf Elvlin's notes say this data needs a newer app version, choose Not now."
    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v8
    new-instance v9, Lcom/exvius/local/UpdatePrompt;
    invoke-direct {v9, v7, v8}, Lcom/exvius/local/UpdatePrompt;-><init>(Landroid/app/Activity;Ljava/lang/String;)V
    invoke-virtual {v7, v9}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    iget-object v7, v9, Lcom/exvius/local/UpdatePrompt;->latch:Ljava/util/concurrent/CountDownLatch;
    invoke-virtual {v7}, Ljava/util/concurrent/CountDownLatch;->await()V
    iget v7, v9, Lcom/exvius/local/UpdatePrompt;->answer:I
    const/4 v8, -0x1
    if-ne v7, v8, :cond_no
    const/4 v8, 0x1
    return v8
    :cond_no
    const/4 v8, -0x2
    if-ne v7, v8, :cond_later
    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v8
    invoke-interface {v8, v3, v0, v1}, Landroid/content/SharedPreferences$Editor;->putLong(Ljava/lang/String;J)Landroid/content/SharedPreferences$Editor;
    move-result-object v8
    invoke-interface {v8}, Landroid/content/SharedPreferences$Editor;->commit()Z
    :cond_later
    const/4 v8, 0x0
    return v8
.end method
