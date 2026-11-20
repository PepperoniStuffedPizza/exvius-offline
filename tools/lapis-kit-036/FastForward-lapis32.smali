.class public final Lcom/exvius/local/FastForward;
.super Ljava/lang/Object;

# interfaces
.implements Landroid/view/View$OnClickListener;
.implements Ljava/lang/Runnable;


# static fields
.field private static base:J

.field private static get:Ljava/lang/reflect/Method;

.field private static level:I

.field private static put:Ljava/lang/reflect/Method;

.field private static shown:Ljava/lang/ref/WeakReference;

.field private static unsafe:Ljava/lang/Object;


# instance fields
.field private armed:J

.field private final btn:Landroid/widget/Button;

.field private final handler:Landroid/os/Handler;

.field private final kind:I

.field private last:I

.field private seen:J


# direct methods
.method private constructor <init>(Landroid/widget/Button;I)V
    .locals 1

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput p2, p0, Lcom/exvius/local/FastForward;->kind:I

    iput-object p1, p0, Lcom/exvius/local/FastForward;->btn:Landroid/widget/Button;

    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object p1

    invoke-direct {v0, p1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    iput-object v0, p0, Lcom/exvius/local/FastForward;->handler:Landroid/os/Handler;

    const/4 v0, 0x2

    invoke-static {v0}, Lcom/exvius/local/FastForward;->peek(I)I

    move-result v0

    iput v0, p0, Lcom/exvius/local/FastForward;->last:I

    return-void
.end method

.method public static attach(Landroid/app/Activity;)V
    .locals 8

    :try_start_0
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Class;->getName()Ljava/lang/String;

    move-result-object v0

    const-string v1, "com.square_enix.android_googleplay.FFBEWW.Lapis"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1

    sget-object v0, Lcom/exvius/local/FastForward;->shown:Ljava/lang/ref/WeakReference;

    if-eqz v0, :cond_0

    invoke-virtual {v0}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;

    move-result-object v0

    if-eq v0, p0, :cond_1

    :cond_0
    new-instance v0, Ljava/lang/ref/WeakReference;

    invoke-direct {v0, p0}, Ljava/lang/ref/WeakReference;-><init>(Ljava/lang/Object;)V

    sput-object v0, Lcom/exvius/local/FastForward;->shown:Ljava/lang/ref/WeakReference;

    const/4 v0, 0x0

    sput v0, Lcom/exvius/local/FastForward;->level:I

    invoke-static {v0}, Lcom/exvius/local/FastForward;->write(I)Z

    invoke-virtual {p0}, Landroid/app/Activity;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    invoke-virtual {v0}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v4

    iget v2, v4, Landroid/util/DisplayMetrics;->widthPixels:I

    iget v3, v4, Landroid/util/DisplayMetrics;->heightPixels:I

    new-instance v0, Landroid/widget/Button;

    invoke-direct {v0, p0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    const-string v1, "Speed: X1"

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    const/high16 v1, 0x41300000    # 11.0f

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setAllCaps(Z)V

    int-to-float v4, v2

    const v5, 0x3e666666    # 0.225f

    mul-float/2addr v4, v5

    float-to-int v4, v4

    invoke-virtual {v0, v4}, Landroid/widget/TextView;->setMinWidth(I)V

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setMinHeight(I)V

    const/high16 v1, 0x3f400000    # 0.75f

    invoke-virtual {v0, v1}, Landroid/view/View;->setAlpha(F)V

    const/16 v1, 0x8

    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V

    new-instance v6, Lcom/exvius/local/FastForward;

    const/4 v7, 0x0

    invoke-direct {v6, v0, v7}, Lcom/exvius/local/FastForward;-><init>(Landroid/widget/Button;I)V

    invoke-virtual {v0, v6}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    new-instance v4, Landroid/widget/FrameLayout$LayoutParams;

    const/4 v5, -0x2

    const/16 v7, 0x33

    invoke-direct {v4, v5, v5, v7}, Landroid/widget/FrameLayout$LayoutParams;-><init>(III)V

    int-to-float v2, v2

    const v5, 0x3ca3d70a    # 0.02f

    mul-float/2addr v2, v5

    float-to-int v2, v2

    iput v2, v4, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    int-to-float v3, v3

    const v5, 0x3f666666    # 0.9f

    mul-float/2addr v3, v5

    float-to-int v3, v3

    iput v3, v4, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {p0, v0, v4}, Landroid/app/Activity;->addContentView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    invoke-virtual {v6}, Lcom/exvius/local/FastForward;->run()V

    new-instance v0, Landroid/widget/Button;

    invoke-direct {v0, p0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    const-string v1, "Finish"

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    const/high16 v1, 0x41300000    # 11.0f

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setAllCaps(Z)V

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setMinHeight(I)V

    const/high16 v1, 0x3f400000    # 0.75f

    invoke-virtual {v0, v1}, Landroid/view/View;->setAlpha(F)V

    const/16 v1, 0x8

    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V

    new-instance v6, Lcom/exvius/local/FastForward;

    const/4 v7, 0x1

    invoke-direct {v6, v0, v7}, Lcom/exvius/local/FastForward;-><init>(Landroid/widget/Button;I)V

    invoke-virtual {v0, v6}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    new-instance v4, Landroid/widget/FrameLayout$LayoutParams;

    const/4 v5, -0x2

    const/16 v7, 0x33

    invoke-direct {v4, v5, v5, v7}, Landroid/widget/FrameLayout$LayoutParams;-><init>(III)V

    const v5, 0x414c0000    # 12.75f

    int-to-float v2, v2

    mul-float/2addr v2, v5

    float-to-int v2, v2

    iput v2, v4, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    iput v3, v4, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {p0, v0, v4}, Landroid/app/Activity;->addContentView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    invoke-virtual {v6}, Lcom/exvius/local/FastForward;->run()V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    :cond_1
    return-void
.end method

.method static base()J
    .locals 4

    new-instance v0, Ljava/io/BufferedReader;

    new-instance v1, Ljava/io/FileReader;

    const-string v2, "/proc/self/maps"

    invoke-direct {v1, v2}, Ljava/io/FileReader;-><init>(Ljava/lang/String;)V

    invoke-direct {v0, v1}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    :cond_0
    invoke-virtual {v0}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;

    move-result-object v1

    if-nez v1, :cond_1

    invoke-virtual {v0}, Ljava/io/BufferedReader;->close()V

    new-instance v1, Ljava/lang/IllegalStateException;

    invoke-direct {v1}, Ljava/lang/IllegalStateException;-><init>()V

    throw v1

    :cond_1
    const-string v2, "/libgame.so"

    invoke-virtual {v1, v2}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_0

    invoke-virtual {v0}, Ljava/io/BufferedReader;->close()V

    const/16 v2, 0x2d

    invoke-virtual {v1, v2}, Ljava/lang/String;->indexOf(I)I

    move-result v2

    const/4 v3, 0x0

    invoke-virtual {v1, v3, v2}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object v1

    const/16 v2, 0x10

    invoke-static {v1, v2}, Ljava/lang/Long;->parseLong(Ljava/lang/String;I)J

    move-result-wide v1

    return-wide v1
.end method

.method static ensure()V
    .locals 5

    sget-object v0, Lcom/exvius/local/FastForward;->put:Ljava/lang/reflect/Method;

    if-eqz v0, :cond_0

    return-void

    :cond_0
    const-string v0, "sun.misc.Unsafe"

    invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v0

    const-string v1, "theUnsafe"

    invoke-virtual {v0, v1}, Ljava/lang/Class;->getDeclaredField(Ljava/lang/String;)Ljava/lang/reflect/Field;

    move-result-object v1

    const/4 v2, 0x1

    invoke-virtual {v1, v2}, Ljava/lang/reflect/Field;->setAccessible(Z)V

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v1

    sput-object v1, Lcom/exvius/local/FastForward;->unsafe:Ljava/lang/Object;

    const/4 v1, 0x1

    new-array v1, v1, [Ljava/lang/Class;

    sget-object v3, Ljava/lang/Long;->TYPE:Ljava/lang/Class;

    const/4 v4, 0x0

    aput-object v3, v1, v4

    const-string v2, "getByte"

    invoke-virtual {v0, v2, v1}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v1

    sput-object v1, Lcom/exvius/local/FastForward;->get:Ljava/lang/reflect/Method;

    const/4 v1, 0x2

    new-array v1, v1, [Ljava/lang/Class;

    aput-object v3, v1, v4

    sget-object v3, Ljava/lang/Byte;->TYPE:Ljava/lang/Class;

    const/4 v4, 0x1

    aput-object v3, v1, v4

    const-string v2, "putByte"

    invoke-virtual {v0, v2, v1}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v0

    invoke-static {}, Lcom/exvius/local/FastForward;->base()J

    move-result-wide v1

    sput-wide v1, Lcom/exvius/local/FastForward;->base:J

    sput-object v0, Lcom/exvius/local/FastForward;->put:Ljava/lang/reflect/Method;

    return-void
.end method

.method private finishClick()V
    .locals 8

    :try_start_0
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v0

    iget-wide v2, p0, Lcom/exvius/local/FastForward;->armed:J

    const-wide/16 v4, 0x0

    cmp-long v6, v2, v4

    if-eqz v6, :cond_0

    sub-long/2addr v2, v0

    neg-long v2, v2

    const-wide/16 v4, 0xbb8

    cmp-long v6, v2, v4

    if-gez v6, :cond_0

    const-wide/16 v4, 0x0

    iput-wide v4, p0, Lcom/exvius/local/FastForward;->armed:J

    const/4 v6, 0x4

    const/4 v7, 0x1

    invoke-static {v6, v7}, Lcom/exvius/local/FastForward;->poke(II)Z

    iget-object v6, p0, Lcom/exvius/local/FastForward;->btn:Landroid/widget/Button;

    const-string v7, "Finish"

    invoke-virtual {v6, v7}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    goto :goto_0

    :cond_0
    iput-wide v0, p0, Lcom/exvius/local/FastForward;->armed:J

    iget-object v6, p0, Lcom/exvius/local/FastForward;->btn:Landroid/widget/Button;

    const-string v7, "Sure?"

    invoke-virtual {v6, v7}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    :goto_0
    return-void
.end method

.method static peek(I)I
    .locals 5

    :try_start_0
    invoke-static {}, Lcom/exvius/local/FastForward;->ensure()V

    sget-wide v0, Lcom/exvius/local/FastForward;->base:J

    int-to-long v2, p0

    add-long/2addr v0, v2

    const-wide/32 v2, 0x4731940

    add-long/2addr v0, v2

    invoke-static {v0, v1}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v0

    const/4 v1, 0x1

    new-array v1, v1, [Ljava/lang/Object;

    const/4 v2, 0x0

    aput-object v0, v1, v2

    sget-object v0, Lcom/exvius/local/FastForward;->get:Ljava/lang/reflect/Method;

    sget-object v2, Lcom/exvius/local/FastForward;->unsafe:Ljava/lang/Object;

    invoke-virtual {v0, v2, v1}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Ljava/lang/Byte;

    invoke-virtual {v0}, Ljava/lang/Byte;->byteValue()B

    move-result v0

    and-int/lit16 v0, v0, 0xff

    return v0
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    const/4 v0, -0x1

    return v0
.end method

.method static poke(II)Z
    .locals 5

    :try_start_0
    invoke-static {}, Lcom/exvius/local/FastForward;->ensure()V

    sget-wide v0, Lcom/exvius/local/FastForward;->base:J

    int-to-long v2, p0

    add-long/2addr v0, v2

    const-wide/32 v2, 0x4731940

    add-long/2addr v0, v2

    invoke-static {v0, v1}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v0

    int-to-byte v1, p1

    invoke-static {v1}, Ljava/lang/Byte;->valueOf(B)Ljava/lang/Byte;

    move-result-object v1

    const/4 v2, 0x2

    new-array v2, v2, [Ljava/lang/Object;

    const/4 v3, 0x0

    aput-object v0, v2, v3

    const/4 v3, 0x1

    aput-object v1, v2, v3

    sget-object v0, Lcom/exvius/local/FastForward;->put:Ljava/lang/reflect/Method;

    sget-object v1, Lcom/exvius/local/FastForward;->unsafe:Ljava/lang/Object;

    invoke-virtual {v0, v1, v2}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    const/4 v0, 0x1

    return v0
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    const/4 v0, 0x0

    return v0
.end method

.method static write(I)Z
    .locals 2

    const/4 v0, 0x0

    invoke-static {v0, p0}, Lcom/exvius/local/FastForward;->poke(II)Z

    move-result v0

    return v0
.end method


# virtual methods
.method public onClick(Landroid/view/View;)V
    .locals 3

    iget v0, p0, Lcom/exvius/local/FastForward;->kind:I

    if-eqz v0, :cond_0

    invoke-direct {p0}, Lcom/exvius/local/FastForward;->finishClick()V

    return-void

    :cond_0
    :try_start_0
    sget v0, Lcom/exvius/local/FastForward;->level:I

    xor-int/lit8 v0, v0, 0x1

    sput v0, Lcom/exvius/local/FastForward;->level:I

    invoke-static {v0}, Lcom/exvius/local/FastForward;->write(I)Z

    move-result v1

    iget-object v2, p0, Lcom/exvius/local/FastForward;->btn:Landroid/widget/Button;

    if-eqz v1, :cond_2

    if-eqz v0, :cond_1

    const-string v0, "Speed x3"

    goto :goto_0

    :cond_1
    const-string v0, "Speed: X1"

    goto :goto_0

    :cond_2
    const-string v0, "Speed: ?"

    :goto_0
    invoke-virtual {v2, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method public run()V
    .locals 10

    :try_start_0
    sget-object v0, Lcom/exvius/local/FastForward;->shown:Ljava/lang/ref/WeakReference;

    if-eqz v0, :cond_5

    invoke-virtual {v0}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;

    move-result-object v0

    iget-object v1, p0, Lcom/exvius/local/FastForward;->btn:Landroid/widget/Button;

    invoke-virtual {v1}, Landroid/view/View;->getContext()Landroid/content/Context;

    move-result-object v2

    if-ne v0, v2, :cond_5

    const/4 v3, 0x2

    invoke-static {v3}, Lcom/exvius/local/FastForward;->peek(I)I

    move-result v3

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v4

    if-gez v3, :cond_0

    const/4 v6, 0x0

    invoke-virtual {v1, v6}, Landroid/view/View;->setVisibility(I)V

    goto :goto_0

    :cond_0
    iget v6, p0, Lcom/exvius/local/FastForward;->last:I

    if-eq v3, v6, :cond_1

    iput v3, p0, Lcom/exvius/local/FastForward;->last:I

    iput-wide v4, p0, Lcom/exvius/local/FastForward;->seen:J

    :cond_1
    iget-wide v6, p0, Lcom/exvius/local/FastForward;->seen:J

    sub-long v6, v4, v6

    const-wide/16 v8, 0xbb8

    cmp-long v6, v6, v8

    if-gez v6, :cond_3

    const/4 v6, 0x0

    invoke-virtual {v1, v6}, Landroid/view/View;->setVisibility(I)V

    iget v6, p0, Lcom/exvius/local/FastForward;->kind:I

    if-eqz v6, :cond_2

    iget-wide v6, p0, Lcom/exvius/local/FastForward;->armed:J

    const-wide/16 v8, 0x0

    cmp-long v8, v6, v8

    if-eqz v8, :cond_4

    sub-long v6, v4, v6

    const-wide/16 v8, 0xbb8

    cmp-long v6, v6, v8

    if-ltz v6, :cond_4

    const-wide/16 v6, 0x0

    iput-wide v6, p0, Lcom/exvius/local/FastForward;->armed:J

    const-string v6, "Finish"

    invoke-virtual {v1, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    goto :goto_0

    :cond_2
    sget v6, Lcom/exvius/local/FastForward;->level:I

    invoke-static {v6}, Lcom/exvius/local/FastForward;->write(I)Z

    goto :goto_0

    :cond_3
    const/16 v6, 0x8

    invoke-virtual {v1, v6}, Landroid/view/View;->setVisibility(I)V

    iget v6, p0, Lcom/exvius/local/FastForward;->kind:I

    if-nez v6, :cond_4

    const/4 v6, 0x0

    invoke-static {v6}, Lcom/exvius/local/FastForward;->write(I)Z

    :cond_4
    :goto_0
    iget-object v6, p0, Lcom/exvius/local/FastForward;->handler:Landroid/os/Handler;

    const-wide/16 v7, 0x12c

    invoke-virtual {v6, p0, v7, v8}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    :cond_5
    return-void
.end method
