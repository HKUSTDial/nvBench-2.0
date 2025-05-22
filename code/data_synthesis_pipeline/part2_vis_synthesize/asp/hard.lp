% ====== Hard constraints ======

% my new rule.
% @hard(multiple_marks_in_view) Only one mark can be used in a view.
violation(multiple_marks_in_view) :-
    entity(view, _, V),
    { entity(mark, V, M) } >= 2.


% @hard(bin_and_aggregate) Cannot bin and aggregate.
violation(bin_and_aggregate) :-
    attribute((encoding,binning),E,_),
    attribute((encoding,aggregate),E,_).

% @hard(aggregate_t_valid) Temporal scale only supports min and max.
violation(aggregate_t_valid) :-
    attribute((field,type),F,datetime),
    helper((encoding,field),E,F),
    attribute((encoding,aggregate),E,A),
    A != min,
    A != max.

% @hard(aggregate_num_valid) Only numbers can be aggregated with mean, sum, stdev
violation(aggregate_num_valid) :-
    attribute((field,type),F,T),
    helper((encoding,field),E,F),
    attribute((encoding,aggregate),E,(mean;sum;stdev)),
    T != number.

% @hard(bin_n_d) Only numbers and datetimes can be binned
violation(bin_n_d) :-
    attribute((field,type),F,T),
    helper((encoding,field),E,F),
    attribute((encoding,binning),E,_),
    T != number,
    T != datetime.

% @hard(aggregate_detail) Detail cannot be aggregated.
violation(aggregate_detail) :-
    attribute((encoding,channel),E,detail),
    attribute((encoding,aggregate),E,_).

% @hard(size_negative) Do not use size when data is negative as size implies that data is positive.
violation(size_negative) :-
    attribute((encoding,channel),E,size),
    helper((encoding,field),E,F),
    attribute((field,min),F,MIN),
    attribute((field,max),F,MAX),
    MIN < 0,
    MAX > 0.

% @hard(encoding_repeat_channel) Cannot use single channels twice for the same mark.
violation(encoding_repeat_channel) :-
    entity(mark,_,M),
    domain(single_channel,C),
    2 <= #count { E : entity(encoding,M,E), attribute((encoding,channel),E,C) }.

% my new rule.
% @hard(encoding_repeat_field) Cannot use the same field twice for the same mark's encodings.
violation(encoding_repeat_field) :-
    entity(mark,_,M),
    attribute((encoding,field),E,F),
    2 <= #count { E1 : entity(encoding,M,E1), attribute((encoding,field),E1,F) }.


% @hard(no_encodings) There has to be at least one encoding for every mark.
violation(no_encodings) :-
    entity(mark,_,M),
    not entity(encoding,M,_).

% @hard(encoding_no_field_and_not_count) All encodings (if they have a channel) require field except if we have a count aggregate.
violation(encoding_no_field_and_not_count) :-
    entity(encoding,_,E),
    not attribute((encoding,field),E,_),
    not attribute((encoding,aggregate),E,count).

% @hard(count_with_field) Count should not have a field. Having a field doesn't make a difference.
violation(count_with_field) :-
    attribute((encoding,aggregate),E,count),
    helper((encoding,field),E,_).

% @hard(text_mark_without_text_channel) Text mark requires text encoding.
violation(text_mark_without_text_channel) :-
    attribute((mark,type),M,text),
    not helper((mark,channel),M,text).

% @hard(text_channel_without_text_mark) Text channel requires text mark.
violation(text_channel_without_text_mark) :-
    helper((mark,channel),M,text),
    not attribute((mark,type),M,text).

% @hard(point_tick_bar_without_x_or_y) Point, tick, and bar require x or y channel.
violation(point_tick_bar_without_x_or_y) :-
    attribute((mark,type),M,(point;tick;bar)),
    not helper((mark,channel),M,x),
    not helper((mark,channel),M,y).

% @hard(line_area_without_x_y) Line and area require x and y channel.
violation(line_area_without_x_y) :-
    attribute((mark,type),M,(line;area)),
    { helper((mark,channel),M,x);helper((mark,channel),M,y) } <= 1.

% my new rule.
% @hard(scatterplot_no_aggregation_xy) Scatterplot (point mark) cannot use aggregation on x or y encodings.
violation(scatterplot_no_aggregation_xy) :-
    attribute((mark,type),M,point),
    entity(encoding,M,E),
    attribute((encoding,channel),E,(x;y)),
    attribute((encoding,aggregate),E,_).

% my new rule
% @hard(scatterplot_no_binning_xy) Scatterplot (point mark) cannot use binning on x or y encodings.
violation(scatterplot_no_binning_xy) :-
    attribute((mark,type),M,point),
    entity(encoding,M,E),
    attribute((encoding,channel),E,(x;y)),
    attribute((encoding,binning),E,_).


% @hard(size_without_point_text) Size only works with some marks.
violation(size_without_point_text) :-
    helper((mark,channel),M,size),
    not attribute((mark,type),M,text),
    not attribute((mark,type),M,point).


% @hard(detail_without_agg) Detail requires aggregation. Detail adds a field to the group by. Detail could also be used to add information to tooltips. We may remove this later.
violation(detail_without_agg) :-
    entity(encoding,M,E1),
    entity(encoding,M,E2),
    E1 != E2,
    attribute((encoding,channel),E1,detail),
    not attribute((encoding,aggregate),E2,_).

% @hard(same_field_x_and_y) Don't use the same field on x and y.
violation(same_field_x_and_y) :-
    helper(mark_channel_field,M,x,F),
    helper(mark_channel_field,M,y,F),
    entity(field,root,F),
    entity(mark,_,M).

% @hard(invalid_bin) Check bin type.
violation(invalid_bin) :-
    attribute((encoding,binning),_,B),
    B < 0.

% @hard(invalid_num_rows) number_rows has to be larger than 0.
violation(invalid_num_rows) :-
    attribute(number_rows,root,R),
    R <= 0.

% @hard(invalid_unique) The number of unique values has to be larger than 0.
violation(invalid_unique) :-
    attribute((field,unique),_,U),
    U <= 0.

% @hard(invalid_extent_non_number) Extent only allowed for numbers (for now).
violation(invalid_extent_non_number) :-
    attribute((field,(min;max)),F,_),
    not attribute((field,type),F,number).

% @hard(invalid_non_number_std) Std only allowed for numbers (for now).
violation(invalid_non_number_std) :-
    attribute((field,std),F,_),
    not attribute((field,type),F,number).

% @hard(invalid_std) Std has to be larger or equal to 0.
violation(invalid_std) :-
    attribute((field,std),_,S),
    S < 0.

% @hard(invalid_extent_order) Order has to be correct.
violation(invalid_extent_order) :-
    attribute((field,min),F,MIN),
    attribute((field,max),F,MAX),
    MIN > MAX.

% @hard(invalid_non_string_freq) Frequency for strings only.
violation(invalid_non_string_freq) :-
    attribute((field,freq),F,_),
    not attribute((field,type),F,string).

% @hard(enforce_order) property should follow natural order for generated entities.
violation(enforce_order):-
    entity(view,root,V), M1 < M2,
    attribute((mark,type),(V,M1),T1),
    attribute((mark,type),(V,M2),T2),
    not T1 < T2.
violation(enforce_order):-
    entity(mark,_,M), E1 < E2,
    attribute((encoding,channel),(M,E1),C1),
    attribute((encoding,channel),(M,E2),C2),
    not C1 < C2.


% my new rules

% Add to hard.lp
% Field must be identifier if unique count equals total rows
violation(invalid_identifier_true) :-
    attribute((field,identifier),F,false),
    attribute((field,unique),F,U),
    attribute(number_rows,root,U).

% Field must not be identifier if unique count doesn't equal total rows
violation(invalid_identifier_false) :-
    attribute((field,identifier),F,true),
    attribute((field,unique),F,U1),
    attribute(number_rows,root,U2),
    U1 != U2.


% ============= mark - encoding ==================
% === MUST HAVE ===

% All marks must have y channel encoding
violation(mark_without_y) :-
    entity(mark,_,M),
    not helper((mark,channel),M,y).

% Specified marks must have x channel encoding
violation(mark_without_x) :-
    attribute((mark,type),M,(bar;line;point;rect;boxplot)),
    not helper((mark,channel),M,x).

% Pie and rect marks must have color channel encoding
violation(mark_without_color) :-
    attribute((mark,type),M,(pie;rect)),
    not helper((mark,channel),M,color).

% === MUST NOT HAVE ===

% Boxplot cannot have color encoding
violation(boxplot_with_color) :-
    attribute((mark,type),M,boxplot),
    helper((mark,channel),M,color).

% Specified marks cannot have size encoding
violation(invalid_mark_with_size) :-
    attribute((mark,type),M,(bar;line;pie;rect;boxplot)),
    helper((mark,channel),M,size).


% ============== mark - encoding - field type ====================

% === Datetime field restrictions ===

% Datetime fields cannot be used with y, color, or size channels for any mark
violation(datetime_invalid_channel) :-
    attribute((field,type),F,datetime),
    helper((encoding,field),E,F),
    attribute((encoding,channel),E,(y;color;size)).

% Datetime fields cannot be used with point, pie, or boxplot marks
violation(datetime_invalid_mark) :-
    attribute((field,type),F,datetime),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,(point;pie;boxplot)).

% === Number field restrictions ===

% Number fields cannot be used with x, color, size for pie and boxplot
violation(number_invalid_pie_boxplot) :-
    attribute((field,type),F,number),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,(pie;boxplot)),
    attribute((encoding,channel),E,(x;color;size)).

% Number fields cannot be used with size for rect
violation(number_invalid_rect) :-
    attribute((field,type),F,number),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,rect),
    attribute((encoding,channel),E,size).

% Number fields cannot be used with color or size for bar and line
violation(number_invalid_bar_line) :-
    attribute((field,type),F,number),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,(bar;line)),
    attribute((encoding,channel),E,(color;size)).

% Number fields cannot be used with color for point
violation(number_invalid_point) :-
    attribute((field,type),F,number),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,point),
    attribute((encoding,channel),E,color).

% === String/Boolean field restrictions ===

% String/Boolean fields cannot be used with y or size for bar and line
violation(discrete_invalid_bar_line) :-
    attribute((field,type),F,(string;boolean)),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,(bar;line)),
    attribute((encoding,channel),E,(y;size)).

% String/Boolean fields cannot be used with x, y, or size for point and pie
violation(discrete_invalid_point_pie) :-
    attribute((field,type),F,(string;boolean)),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,(point;pie)),
    attribute((encoding,channel),E,(x;y;size)).

% String/Boolean fields cannot be used with color or size for rect
violation(discrete_invalid_rect) :-
    attribute((field,type),F,(string;boolean)),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,rect),
    attribute((encoding,channel),E,(color;size)).

% String/Boolean fields cannot be used with y, color, or size for boxplot
violation(discrete_invalid_boxplot) :-
    attribute((field,type),F,(string;boolean)),
    helper((encoding,field),E,F),
    entity(encoding,M,E),
    attribute((mark,type),M,boxplot),
    attribute((encoding,channel),E,(y;color;size)).

% ============== binning ====================

% Only bar, line, rect marks can have binning on x channel
violation(invalid_binning_x) :-
    entity(encoding,M,E),
    attribute((encoding,binning),E,_),
    attribute((encoding,channel),E,x),
    attribute((mark,type),M,T),
    T != bar,
    T != line,
    T != rect.

% Only rect mark can have binning on y channel
violation(invalid_binning_y) :-
    entity(encoding,M,E),
    attribute((encoding,binning),E,_),
    attribute((encoding,channel),E,y),
    attribute((mark,type),M,T),
    T != rect.

% Binning not allowed on color or size channels
violation(binning_invalid_channel) :-
    entity(encoding,_,E),
    attribute((encoding,binning),E,_),
    attribute((encoding,channel),E,(color;size)).

% ============== aggregate ====================

% String/boolean fields cannot be aggregated
violation(invalid_field_aggregate) :-
    attribute((field,type),F,(string;boolean)),
    helper((encoding,field),E,F),
    attribute((encoding,aggregate),E,_).

% Note: count_with_field already exists in hard.lp
% Note: encoding_no_field_and_not_count already exists in hard.lp

% Aggregation not allowed on x channel
violation(aggregate_on_x) :-
    entity(encoding,_,E),
    attribute((encoding,channel),E,x),
    attribute((encoding,aggregate),E,_).

% For bar, line, pie marks, aggregate only allowed on y channel
violation(invalid_aggregate_channel_mark1) :-
    entity(encoding,M,E),
    attribute((mark,type),M,(bar;line;pie)),
    attribute((encoding,aggregate),E,_),
    attribute((encoding,channel),E,C),
    C != y.

% For rect marks, aggregate only allowed on color channel
violation(invalid_aggregate_channel_mark2) :-
    entity(encoding,M,E),
    attribute((mark,type),M,rect),
    attribute((encoding,aggregate),E,_),
    attribute((encoding,channel),E,C),
    C != color.

% For point marks, aggregate only allowed on size channel
violation(invalid_aggregate_channel_mark3) :-
    entity(encoding,M,E),
    attribute((mark,type),M,point),
    attribute((encoding,aggregate),E,_),
    attribute((encoding,channel),E,C),
    C != size.

% Boxplot marks cannot have any aggregation
violation(boxplot_with_aggregate) :-
    entity(encoding,M,E),
    attribute((mark,type),M,boxplot),
    attribute((encoding,aggregate),E,_).

% ============== identifier - binning - aggregate ====================

% === Bar and Line rules ===
% If x encoding has non-identifier field, y must aggregate
violation(bar_line_y_must_aggregate_non_id) :-
    attribute((mark,type),M,(bar;line)),
    entity(encoding,M,EX),
    entity(encoding,M,EY),
    attribute((encoding,channel),EX,x),
    attribute((encoding,channel),EY,y),
    helper((encoding,field),EX,F),
    attribute((field,identifier),F,false),
    not attribute((encoding,aggregate),EY,_).

% If x encoding has binning, y must aggregate
violation(bar_line_y_must_aggregate_binning) :-
    attribute((mark,type),M,(bar;line)),
    entity(encoding,M,EX),
    entity(encoding,M,EY),
    attribute((encoding,channel),EX,x),
    attribute((encoding,channel),EY,y),
    attribute((encoding,binning),EX,_),
    not attribute((encoding,aggregate),EY,_).

% If (x encoding has identifier field and no binning) and y has field, y must not aggregate
violation(bar_line_y_must_not_aggregate) :-
    attribute((mark,type),M,(bar;line)),
    entity(encoding,M,EX),
    entity(encoding,M,EY),
    attribute((encoding,channel),EX,x),
    attribute((encoding,channel),EY,y),
    helper((encoding,field),EX,F),
    attribute((field,identifier),F,true),
    not attribute((encoding,binning),EX,_),
    helper((encoding,field),EY,_),  % Added condition: y has field
    attribute((encoding,aggregate),EY,_).

% === Pie rules ===
% If color encoding has non-identifier field, y must aggregate
violation(pie_y_must_aggregate_non_id) :-
    attribute((mark,type),M,pie),
    entity(encoding,M,EC),
    entity(encoding,M,EY),
    attribute((encoding,channel),EC,color),
    attribute((encoding,channel),EY,y),
    helper((encoding,field),EC,F),
    attribute((field,identifier),F,false),
    not attribute((encoding,aggregate),EY,_).

% If color encoding has binning, y must aggregate
violation(pie_y_must_aggregate_binning) :-
    attribute((mark,type),M,pie),
    entity(encoding,M,EC),
    entity(encoding,M,EY),
    attribute((encoding,channel),EC,color),
    attribute((encoding,channel),EY,y),
    attribute((encoding,binning),EC,_),
    not attribute((encoding,aggregate),EY,_).

% If color encoding has identifier field and no binning and y has field, y must not aggregate
violation(pie_y_must_not_aggregate) :-
    attribute((mark,type),M,pie),
    entity(encoding,M,EC),
    entity(encoding,M,EY),
    attribute((encoding,channel),EC,color),
    attribute((encoding,channel),EY,y),
    helper((encoding,field),EC,F),
    attribute((field,identifier),F,true),
    not attribute((encoding,binning),EC,_),
    helper((encoding,field),EY,_),  % Added condition: y has field
    attribute((encoding,aggregate),EY,_).

% % === Point rules ===
% % If any encoding in [x, y, color] has identifier field, size must not aggregate
% violation(point_size_must_not_aggregate) :-
%     attribute((mark,type),M,point),
%     entity(encoding,M,E1),
%     entity(encoding,M,ES),
%     attribute((encoding,channel),E1,(x;y;color)),
%     attribute((encoding,channel),ES,size),
%     helper((encoding,field),E1,F),
%     attribute((field,identifier),F,true),
%     attribute((encoding,aggregate),ES,_).

% % === Rect rules ===
% % If any encoding in [x, y] has binning, color must aggregate
% violation(rect_color_must_aggregate) :-
%     attribute((mark,type),M,rect),
%     entity(encoding,M,E1),
%     entity(encoding,M,EC),
%     attribute((encoding,channel),E1,(x;y)),
%     attribute((encoding,channel),EC,color),
%     attribute((encoding,binning),E1,_),
%     not attribute((encoding,aggregate),EC,_).

% % If any encoding in [x, y] has identifier field and no binning, color must not aggregate
% violation(rect_color_must_not_aggregate) :-
%     attribute((mark,type),M,rect),
%     entity(encoding,M,E1),
%     entity(encoding,M,EC),
%     attribute((encoding,channel),E1,(x;y)),
%     attribute((encoding,channel),EC,color),
%     helper((encoding,field),E1,F),
%     attribute((field,identifier),F,true),
%     not attribute((encoding,binning),E1,_),
%     attribute((encoding,aggregate),EC,_).


% do binning when unique number > 20
% For bar/line/rect marks, must bin x channel if numeric/datetime field has > 20 unique values
violation(require_binning_x) :-
    attribute((mark,type),M,(bar;line;rect)),
    entity(encoding,M,E),
    attribute((encoding,channel),E,x),
    helper((encoding,field),E,F),
    attribute((field,type),F,(datetime;number)),
    attribute((field,unique),F,U),
    U > 20,
    not attribute((encoding,binning),E,_).

% For bar/line/rect marks, must NOT bin x channel if numeric/datetime field has <= 20 unique values
violation(require_binning_x) :-
    attribute((mark,type),M,(bar;line;rect)),
    entity(encoding,M,E),
    attribute((encoding,channel),E,x),
    helper((encoding,field),E,F),
    attribute((field,type),F,(datetime;number)),
    attribute((field,unique),F,U),
    U <= 20,
    attribute((encoding,binning),E,_).

% For rect mark, must bin y channel if numeric field has > 20 unique values
violation(require_binning_y) :-
    attribute((mark,type),M,rect),
    entity(encoding,M,E),
    attribute((encoding,channel),E,y),
    helper((encoding,field),E,F),
    attribute((field,type),F,number),
    attribute((field,unique),F,U),
    U > 20,
    not attribute((encoding,binning),E,_).

% For rect mark, must NOT bin y channel if numeric field has <= 20 unique values
violation(require_binning_y) :-
    attribute((mark,type),M,rect),
    entity(encoding,M,E),
    attribute((encoding,channel),E,y),
    helper((encoding,field),E,F),
    attribute((field,type),F,number),
    attribute((field,unique),F,U),
    U <= 20,
    attribute((encoding,binning),E,_).


% Enforce x/y channel assignment ordering based on field indices for point and rect marks
violation(field_order_xy) :-
    entity(mark,_,M),
    attribute((mark,type),M,(point;rect)),
    helper(mark_channel_field,M,x,F1),
    helper(mark_channel_field,M,y,F2),
    attribute((field,type),F1,(number;string;boolean)),
    attribute((field,type),F2,(number;string;boolean)),
    F1 > F2.

% Rect mark's color encoding cannot have field (only aggregate count)
violation(rect_color_no_field) :-
    attribute((mark,type),M,rect),
    entity(encoding,M,E),
    attribute((encoding,channel),E,color),
    helper((encoding,field),E,_).