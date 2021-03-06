# DATA_SYNC
MySQL、MongoDB向Postgresql数据迁移

## remarks：
   本程序主要进行MySQL到PostgreSQL以及MongoDB到PostgreSQL的数据平行迁移，以数据的最后更新时间（最后修改时间）作为时间节点，可选择某一区间内的数据进行迁移。

## 实现原理：
  ### MySQL ------→ PostgreSQL
1. 基础字段：采用一对一进行映射对应，然后同步相关数据，注意源表id字段，不能直接同步到postgresql的id字段中，odoo中postgresql的id字段为自增主键，可使用其他字段来对应源表id字段，如origin_id等。 
2. 外键字段：由于odoo中postgresql的外键字段存储主表的主键（自增id），直接同步关联关系无法关联，该程序采用两个字段（a字段，b字段）来添加关联关系，
         a字段对应源表中外键字段，然后使用该字段值在目标表被引用的表（主表）中查询所对应的id（select id from 目标表关联主表 where origin_id = a值），origin_id为源表关联主表主键字段对应的目标表关联主表字段，由于它的唯一性，所以直接将查询出的一个id值保存到b字段（目标表新的外键字段）中即可，这样即可保证关联关系成立。

### MongoDB ------→ PostgreSQL
采用一对一字段映射同步，由于文档是 MongoDB 中数据的基本单位，类似于关系数据库中的行（但是比行复杂），多个键及其关联的值有序地放在一起就构成了文档。  
 一个文档包含一组field（字段），每一个字段都是一个key/value。key必须为字符串类型。value可以包含如下类型：
 * 基本类型，例如，string，int，float，timestamp，binary 等类型。
 * 一个文档。
 * 数组类型。  
 key即为postgresql中的字段名，value类型即为字段类型，由于postgresql不支持文档，数组等类型，因此采用text类型进行替代。另外MongoDB中如果使用的是默认的_id，它是一个ObjectId字段，postgresql不支持，采用char类型进行转换。  
   <font color=red>本程序尚未添加MongoDB主外键关联同步，同一类不同模式的文档都放在同一个集合中。</font>

## 操作说明：
1. 数据库信息填入，填写需要同步的源数据库相关信息以及目标数据库相关信息， 如IP地址，端口号，登录用户名，密码等，具体信息如下：
    * 数据库名称：输入数据库名称，如test；
    * 数据库主机（ip）：输入数据库连接ip，如localhost；
    * 端口号：输入数据库连接端口号，如3306；
    * 数据库登录用户名：输入数据库连接登录用户名称，如root；
    * 数据库登录密码：输入数据库连接密码，如123456；
    * 生效状态：是否生效；
    * 数据库描述：添加对于该数据库的描述；
    * 数据库类型：下拉框，选择该数据库类型，如MySQL。

2. 同步表信息填入，填写需要同步的源表（集合）以及目标表相关信息，如表名称等，具体信息如下：
    * 数据库：下拉框，选择上一步中填入的数据库；
    * 同步表名称：输入需要同步的表名称，如student；
    * 生效状态：是否生效；
    * 映射状态：如果该表是目标表且为配置表，可选择映射状态为True，方便主外键关联时快速查询；
    * 表描述：添加对于该表的描述，如目标学生表；
    * 数据库描述：自动带出。   
    <font color=red>注意：表和数据库是一一对应的关系，即选择源数据库填写源表信息，目标数据库填写目标表信息。</font>

3. 同步表映射关系填入，选择上一步填写的同步表，目标表，然后选择同步顺序，开始以及结束同步时间， 生效状态，以及分组等信息，具体信息如下：
    * 源同步表：选择上一步填写的表（源表）；
    * 源同步表描述：自动带出；
    * 目标同步表：选择上一步填写的表（目标表）；
    * 目标同步表描述：自动带出；
    * 同步顺序：填写同步顺序，参考：基础表（1 - 99），主表（100 - 999），从表（1000 - 9999）；
    * 开始同步时间：选择同步数据时间区间的开始节点；
    * 结束同步时间：选择同步数据时间区间的结束节点；
    * 生效状态：是否生效；
    * 分组：同步数据分组进行，共4组，对应四个定时任务，可按不同分类分组进行。

4. 需要同步的字段映射关系填入，填写相关字段的名称，类型，以及是否是唯一字段，是否生效，以及是否是时间节点字段（最后更新（修改）时间等，具体信息如下：
    * 同步表映射关系：下拉框，选择上一步填写的同步表映射关系；
    * 源同步表名称：自动带出；
    * 源同步表字段名称：填写需要同步的源表字段（单个填写），如name；
    * 源同步表字段类型：填写源同步表字段的字段类型，如varchar；
    * 源字段描述：填写源同步表字段的描述信息， 如源表学生姓名；
    * 目标同步表名称：自动带出；
    * 目标同步表字段名称：填写与源表字段对应的目标表字段（单个填写）如name；
    * 目标同步表字段类型：填写目标同步表的字段类型，如varchar；
    * 目标字段描述：添加目标字段的描述信息，如目标表学生 姓名；
    * 唯一标识：唯一标识字段，即该字段是否是源表主键；
    * 生效状态：是否生效；
    * 时间节点：时间节点字段，如是否是最后更新（修改）时间字段。

5. 目标表主外键关联关系信息填入，如主表，主表主键，从表，从表外键等（mysql-→postgresql），具体信息如下：
    * 同步表映射关系：下拉框，选择同步表映射关系中的数据；
    * 目标表关联主表：下拉框，选择目标表外键字段关联的主表，如teacher；
    * 主表主键：填写目标表外键字段参考（关联）字段， 如id；
    * 源表主键：填写源主表的主键字段在目标主表的对应字段， 如origin_id；
    * 目标表：下拉框，选择同步的目标表，如student；
    * 外键：填写目标表的外键字段，如teacher_id；
    * 源表外键：填写源表的外键字段在目标表中的对应字段, 如origin_teacher_id；
    * 生效状态：是否生效。

6. 主外键关联任务表，由程序自动添加数据，我们可以查看相关信息，不允许新建，编辑。  
    该部分主要显示主外键补偿任务相关信息，即当从表数据已同步，但主表数据尚未同步，主外键无法关联上时，会将相关信息保存到此处，等主表数据同步之后，使用定时任务扫描该张表，将相关主外键进行关联。
   
## 定时任务
主同步任务分为四组，可根据需要进行分类分组同步，补偿任务四组，提高同步效率，MongoDB同步到PostgreSQL，无需开启补偿任务。   
首次安装应用时定时任务默认一天执行一次，下次执行日期为应用安装日期（UTC时区），可根据需要调整参数，状态关闭，需要手动打开定时任务。      
<font color=red>注意：odoo的定时任务时间计算为UTC时区时间，所以在调整下一执行日期时需要注意时间间隔，或者将时区时间改为当前时区时间。</font>